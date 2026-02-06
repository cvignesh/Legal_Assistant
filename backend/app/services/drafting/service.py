import asyncio
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from app.core.config import settings
from app.services.retrieval.hybrid_search import hybrid_search_service
from app.services.retrieval.models import SearchQuery
from app.services.drafting.models import (
    DraftingRequest, DraftingResponse, FactExtractionResult, 
    LegalIssue, ValidatedCitation, DocumentType
)
from app.services.drafting.prompts import FACT_EXTRACTION_PROMPT, LEGAL_MAPPING_PROMPT
from app.services.drafting.rules import DraftingRules
from app.services.drafting.validator import ProceduralValidator
from app.services.drafting.templates import (
    POLICE_COMPLAINT_TEMPLATE, MAGISTRATE_156_3_TEMPLATE,
    PRIVATE_COMPLAINT_TEMPLATE, LEGAL_NOTICE_TEMPLATE
)
from app.services.drafting.substantive import substantive_validator

logger = logging.getLogger(__name__)

class DraftingService:
    def __init__(self):
        # Initialize LLM (reuse config from ViabilityService)
        provider = settings.LLM_PROVIDER.lower()
        if provider == "groq":
            self.llm = ChatGroq(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.1
            )
        else:
             self.llm = ChatOpenAI(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.1
            )
        
        logger.info("DraftingService initialized")

    async def _extract_facts(self, user_story: str) -> FactExtractionResult:
        """Step 1: Extract structured facts using LLM"""
        try:
            prompt = FACT_EXTRACTION_PROMPT.format(user_story=user_story)
            response = await asyncio.to_thread(
                self.llm.invoke,
                [SystemMessage(content="You are a JSON-outputting legal assistant."), HumanMessage(content=prompt)]
            )
            # Robust JSON extraction
            content = response.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]

            return FactExtractionResult.model_validate_json(content)
        except Exception as e:
            logger.error(f"Fact Extraction Failed: {e}")
            raise ValueError("Failed to extract facts from user story.")

    async def _identify_legal_issues(self, facts: FactExtractionResult) -> List[LegalIssue]:
        """Step 2: Map facts to legal sections using LLM"""
        try:
            facts_json = facts.model_dump_json()
            prompt = LEGAL_MAPPING_PROMPT.format(facts_json=facts_json)
            response = await asyncio.to_thread(
                self.llm.invoke,
                [SystemMessage(content="You are a JSON-outputting legal assistant."), HumanMessage(content=prompt)]
            )
            # Robust JSON extraction
            content = response.content.strip()
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]
                
            # Expecting a list of objects
            import json
            data = json.loads(content)
            return [LegalIssue(**item) for item in data]
        except Exception as e:
            logger.error(f"Legal Mapping Failed: {e}")
            return [] # Fallback to empty

    async def _verify_statute(self, issue: LegalIssue) -> bool:
        """Step 3a: Verify statute exists and fetch complete section details (MongoDB Primary -> Hybrid Fallback)"""
        # Map common act names to database format
        act_mapping = {
            "NEGOTIABLE INSTRUMENTS ACT": "NI_ACT",
            "NI ACT": "NI_ACT",
            "NEGOTIABLE INSTRUMENTS ACT, 1881": "NI_ACT",
            "BNS": "BNS",
            "IPC": "IPC",
            "CRPC": "CrPC"
        }
        
        act_short = act_mapping.get(issue.act.upper(), issue.act.upper())
        
        # Get MongoDB database reference (lazy access)
        from app.db.mongo import mongo
        db = mongo.db
        
        # Ensure section_id is a string (MongoDB stores it as string)
        section_id = str(issue.section)
        
        logger.info(f"Querying MongoDB for: act_short={act_short}, section_id={section_id}")
        
        # --- ATTEMPT 1: Direct MongoDB Lookup (Best Quality) ---
        collection = db["legal_documents"]
        
        # Find all chunks for this section (async cursor)
        cursor = collection.find({
            "metadata.act_short": act_short,
            "metadata.section_id": section_id
        }).sort("metadata.chunk_type", 1)
        
        section_chunks = await cursor.to_list(length=None)
        
        section_title = ""
        section_full_text = ""
        punishment_text = ""
        
        if section_chunks:
            logger.info(f"✓ Found {len(section_chunks)} chunks in MongoDB for {act_short} Section {issue.section}")
            
            # Combine all chunks
            section_parts = []
            for chunk in section_chunks:
                meta = chunk.get("metadata", {})
                content = chunk.get("raw_content", "")
                
                # Extract section title
                if not section_title and meta.get("section_title"):
                    section_title = meta["section_title"]
                
                # Add content with labels
                chunk_type = meta.get("chunk_type", "Section")
                if chunk_type == "Section":
                    section_parts.append(content)
                elif chunk_type == "Illustration":
                    section_parts.append(f"\n\n**Illustration:**\n{content}")
                elif chunk_type == "Explanation":
                    section_parts.append(f"\n\n**Explanation:**\n{content}")
                elif chunk_type == "Proviso":
                    section_parts.append(f"\n\n**Proviso:**\n{content}")
                else:
                    section_parts.append(f"\n\n{content}")
                
                # Check for punishment
                if "punishment" in content.lower() or "imprisonment" in content.lower() or "fine" in content.lower():
                    if not punishment_text:
                        punishment_text = content
            
            section_full_text = "\n".join(section_parts)
            
        else:
            # --- ATTEMPT 2: Hybrid Search Fallback (Robustness) ---
            logger.warning(f"Statute {act_short} Section {section_id} not found in MongoDB - Attempting Hybrid Search Fallback")
            
            query_text = f"{issue.act} Section {issue.section}"
            
            # Use filters if possible to narrow down
            filters = {"metadata.act_short": act_short} if act_short != issue.act.upper() else {}
            
            search_query = SearchQuery(
                query=query_text,
                top_k=3, # Fetch top 3 to catch split chunks (e.g. explanations)
                filters=filters,
                document_type=None
            )
            
            results = await hybrid_search_service.search(search_query)
            
            if results.results:
                valid_chunks = []
                for res in results.results:
                    # Only include if score is decent
                         if res.score > 0.3:
                            valid_chunks.append(res.text_for_embedding)
                            # Capture title from the best match
                         if not section_title:
                             section_title = res.metadata.get("section_title", "")
                
                if valid_chunks:
                    logger.info(f"✓ Found {len(valid_chunks)} chunks via Hybrid Search")
                    section_full_text = "\n\n".join(valid_chunks)
                    
                    # Try to extract punishment from the combined text
                    if "punishment" in section_full_text.lower() or "imprisonment" in section_full_text.lower():
                        punishment_text = "Refer to full text for punishment details."
                else:
                    logger.warning(f"Hybrid search results found but scores too low (Top: {results.results[0].score:.2f})")

        # Update the issue object
        if section_full_text:
             issue.section_title = section_title
             issue.section_full_text = section_full_text
             issue.punishment = punishment_text
             issue.is_validated = True
             return True
        else:
             logger.warning("Statute details could not be retrieved from DB or Search.")
             issue.is_validated = False
             # Return True so it's included in the response (as an unvalidated risk)
             return True 

    async def _get_grounded_judgments(self, issues: List[LegalIssue]) -> List[ValidatedCitation]:
        """Step 3b: Fetch judgments strictly from Vector DB"""
        citations = []
        
        for issue in issues:
            # 1. Verify Statute First
            is_valid_statute = await self._verify_statute(issue)
            if not is_valid_statute:
                logger.warning(f"Statute {issue.act} {issue.section} not verified. Skipping judgment search.")
                continue

            # 2. Search for Precedents using FACTS + SECTION (not just section)
            # This provides better semantic matching based on the actual legal issue
            query_text = f"{issue.reasoning} {issue.act} Section {issue.section}"
            
            # Fallback to simpler query if reasoning is too generic
            if len(issue.reasoning.split()) < 5:
                if issue.act.upper() == "BNS":
                    query_text = f"BNS Section {issue.section}"
                elif "NEGOTIABLE" in issue.act.upper() or "NI ACT" in issue.act.upper():
                    query_text = f"Section 138 cheque dishonour"
                else:
                    query_text = f"{issue.act} Section {issue.section}"
            
            # Filter by document_type only (MongoDB Atlas Search doesn't support $in in filters)
            filters = {
                "document_type": "judgment"
            }
                
            query = SearchQuery(
                query=query_text,
                top_k=5,  # Increased to get more results before filtering
                filters=filters,
                document_type="judgment"
            )
            
            logger.info(f"Searching judgments for: {query_text[:100]}...")
            results = await hybrid_search_service.search(query)
            logger.info(f"Found {len(results.results)} judgment results for {issue.act} Section {issue.section}")
            
            for res in results.results:
                # Very relaxed threshold since reranker is already strict
                if res.score < 0.2:
                    logger.debug(f"Skipping result with score {res.score:.2f}")
                    continue
                    
                meta = res.metadata
                
                # Handle missing metadata fields with proper fallbacks
                case_title = meta.get("case_title") or meta.get("case_name") or "Unknown Case"
                doc_url = meta.get("doc_url") or meta.get("source_url") or "Internal DB"
                
                # Extract PDF URL
                pdf_url = meta.get("pdf_url") or meta.get("doc_url") or meta.get("source_url") or meta.get("file_path")
                
                # Generate relevance explanation using LLM
                relevance_explanation = await self._explain_citation_relevance(
                    user_issue=issue,
                    judgment_excerpt=res.text_for_embedding[:500],
                    case_title=case_title
                )
                
                citation = ValidatedCitation(
                    case_title=case_title,
                    citation_source=doc_url,
                    excerpt=res.text_for_embedding[:800] + "...",  # Increased from 300 to 800
                    relevance_score=res.score,
                    relevance_explanation=relevance_explanation,
                    pdf_url=pdf_url
                )
                citations.append(citation)
                logger.info(f"Added citation: {citation.case_title} (score: {res.score:.2f})")
        
        # Deduplicate by title
        seen = set()
        unique_citations = []
        for c in citations:
            if c.case_title not in seen:
                seen.add(c.case_title)
                unique_citations.append(c)
                
        logger.info(f"Found {len(unique_citations)} unique grounded citations")
        return unique_citations[:3]  # Max 3 citations
    
    async def _explain_citation_relevance(self, user_issue: LegalIssue, judgment_excerpt: str, case_title: str) -> str:
        """Generate explanation of why this precedent is relevant to user's case"""
        prompt = f"""You are a legal expert. Explain in 2-3 concise sentences why the following precedent is relevant to the user's case.

USER'S LEGAL ISSUE:
Act: {user_issue.act}
Section: {user_issue.section}
Reasoning: {user_issue.reasoning}

PRECEDENT CASE:
Title: {case_title}
Excerpt: {judgment_excerpt}

Explain how this precedent supports or relates to the user's case. Focus on:
1. Similar facts or legal issues
2. How the court's reasoning applies
3. What legal principle it establishes

Keep it concise and practical."""

        response = await self.llm.ainvoke(prompt)
        return response.content.strip()

    def _apply_rules_and_format(
        self, 
        request: DraftingRequest, 
        facts: FactExtractionResult, 
        issues: List[LegalIssue], 
        citations: List[ValidatedCitation]
    ) -> str:
        """Step 4 & 5: Rule Engine + Template Filling"""
        doc_type = request.document_type.value
        rules = DraftingRules.get_rules(doc_type)
        
        # 1. Prepare Data for Template
        
        # Chronology
        chronology_text = ""
        for i, event in enumerate(facts.chronology, 1):
             chronology_text += f"{i}. {event}\n"
             
        # Legal Sections
        sections_text = ""
        for issue in issues:
            sections_text += f"- Section {issue.section} of {issue.act}: {issue.reasoning}\n"
            
        # Citations (Check Rule)
        include_citations = DraftingRules.should_include_citations(doc_type)
        citation_text = ""
        if include_citations and citations:
            for i, cite in enumerate(citations, 1):
                # Extract clean content without metadata headers
                # Remove lines starting with "Case:", "Section:", "Role:", "Topics:", "Content:", "Quote:"
                clean_excerpt = cite.excerpt
                for prefix in ["Case:", "Section:", "Role:", "Topics:", "Content:", "Quote:", "Excerpt:"]:
                    if prefix in clean_excerpt:
                        # Take content after the metadata line
                        parts = clean_excerpt.split(prefix, 1)
                        if len(parts) > 1:
                            clean_excerpt = parts[1].strip()
                
                # Remove metadata lines (lines with " | " pattern)
                lines = clean_excerpt.split('\n')
                clean_lines = [line for line in lines if ' | ' not in line or len(line) > 100]
                clean_excerpt = '\n'.join(clean_lines).strip()
                
                # Remove trailing dots to avoid double ellipsis
                clean_excerpt = clean_excerpt.rstrip('.')
                
                citation_text += f"{i}. {cite.case_title}\n\n"
                citation_text += f"   {cite.relevance_explanation}\n\n"
                citation_text += f"   The Hon'ble Court observed: \"{clean_excerpt[:400]}...\"\n\n"
        elif include_citations and not citations:
            citation_text = "(No relevant high-confidence judgments found in database)"
        else:
            citation_text = "[Citations omitted as per document format]"
            
        # Context Dict
        context = {
            "city": facts.place_of_occurence or "[City]",
            "police_station_name": "[Police Station Name]", # Needs user input or inference
            "date_of_occurence": facts.date_of_occurence or "[Date]",
            "place_of_occurence": facts.place_of_occurence or "[Location]",
            "monetary_details": facts.monetary_details or "[Amount]",
            "core_allegation": facts.core_allegation,
            "accused_name": facts.accused_details or "[Accused Name]",
            "accused_address": "[Accused Address]",
            "complainant_name": facts.complainant_details or "[Your Name]",
            "complainant_address": "[Your Address]",
            "current_date": "2024-XX-XX", # Dynamic date
            "state": "[State]",
            
            # Dynamic Blocks
            "chronology_bullets": chronology_text,
            "legal_sections_list": sections_text,
            "citations_section": citation_text
        }
        
        # 2. Select Template
        if doc_type == "police_complaint":
            template = POLICE_COMPLAINT_TEMPLATE
        elif doc_type == "magistrate_156_3":
            template = MAGISTRATE_156_3_TEMPLATE
        elif doc_type == "private_complaint_200":
            template = PRIVATE_COMPLAINT_TEMPLATE
        elif doc_type == "legal_notice":
            template = LEGAL_NOTICE_TEMPLATE
        else:
            return "Document type not supported."
            
        # 3. Render
        return template.safe_substitute(context)

    async def generate_draft(self, request: DraftingRequest) -> DraftingResponse:
        """Main Orchestrator"""
        
        # Step 1: Fact Extraction
        facts = await self._extract_facts(request.user_story)
        
        # Step 2: Legal Mapping
        issues = await self._identify_legal_issues(facts)
        
        # Step 3: Grounding (Statute + Judgment)
        # Verify statutes are real (filter out hallucinations)
        valid_issues = []
        warnings = []
        for issue in issues:
            if await self._verify_statute(issue):
                valid_issues.append(issue)
            else:
                warnings.append(f"Statute {issue.act} {issue.section} could not be verified in the database.")
        
        # Fetch judgments for valid issues
        citations = await self._get_grounded_judgments(valid_issues)
        
        # Step 3.5: Procedural Verification
        procedural_analysis = ProceduralValidator.validate(request.document_type, facts, issues, citations)

        # Step 3.6: Substantive Analysis (Senior Lawyer Review)
        substantive_gaps = await substantive_validator.analyze(request.user_story, issues)
        
        # Step 4: Drafting
        # Pass ALL issues to drafting, even if unverified (users might know better than empty DB)
        final_text = self._apply_rules_and_format(request, facts, issues, citations)
        
        return DraftingResponse(
            draft_text=final_text,
            facts=facts,
            legal_issues=issues, # Return all identified issues
            citations=citations,
            validation_warnings=warnings,
            procedural_analysis=procedural_analysis,
            substantive_analysis=substantive_gaps
        )

drafting_service = DraftingService()
