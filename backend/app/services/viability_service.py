"""
Viability Predictor Service
Predicts case outcome probability based on similar historical judgments.
"""
from typing import List, Dict, Any, Optional
import asyncio
import json
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.retrieval.hybrid_search import hybrid_search_service
from app.services.retrieval.models import SearchQuery

# --- PROMPTS ---

FACT_EXTRACTION_System_PROMPT = """
You are a Legal Assistant. 
Task: Extract "Key Legal Facts" from the user's unstructured input to form a structured search query.
Focus on:
1. Core Offence/Act (e.g., Section 138 NI Act, Murder 302 IPC)
2. Key Defense/Argument (e.g., Signature Mismatch, Alibi, Delay in FIR)
3. Procedural Status (e.g., Notice Warning, Bail Application)

Output strictly the core facts in a single precise sentence. 
Do not add introduction or explanation.
"""

STRATEGIC_ANALYSIS_SYSTEM_PROMPT = """
You are a Senior Legal Strategist.
Task: Analyze the user's case viability based on these similar precedents.

Input:
1. User Facts
2. Top 3 Similar Case Summaries (with Outcomes and Scores)

Instructions:
1. Compare the core facts of the precedents with the user's case.
2. Identify the *differentiating factor* that led to the outcome (Winning Point vs Losing Point).
3. Provide a clear "Strategic Advice" paragraph explaining WHY the user might win or lose.
4. Cite specific cases if relevant.

Output Format: A single concise paragraph (max 150 words).
"""

# --- MODELS ---

class PredictionResult(BaseModel):
    viability_score: float  # 0 to 100
    viability_label: str    # "High", "Medium", "Low"
    total_analyzed: int
    favorable_count: float  # Weighted count
    top_precedents: List[Dict[str, Any]]
    strategic_advice: str

class ViabilityService:
    def __init__(self):
        # Initialize LLM
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

    async def _extract_key_facts(self, raw_input: str) -> str:
        """Step 1: Convert raw rant into structured legal facts"""
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=FACT_EXTRACTION_System_PROMPT),
                    HumanMessage(content=raw_input)
                ]
            )
            return response.content.strip()
        except Exception as e:
            print(f"Fact extraction failed: {e}")
            return raw_input  # Fallback to raw input

    async def _generate_advice(self, user_facts: str, top_cases: List[Dict], stats: Dict[str, float]) -> str:
        """Step 4: Generate strategic insight using LLM"""
        try:
            # Format top cases for prompt
            case_summaries = ""
            for i, case in enumerate(top_cases[:3], 1):
                meta = case.get("metadata", {})
                case_summaries += (
                    f"{i}. {meta.get('case_title')} ({meta.get('year_of_judgment')})\n"
                    f"   Outcome: {meta.get('outcome')} | Similarity: {case.get('score'):.2f}\n"
                    f"   Context: {case.get('text_for_embedding')[:200]}...\n\n"
                )
            
            # Contextualize with overall stats
            stats_context = (
                f"Overall Viability Score: {stats['score']:.1f}%\n"
                f"Total Similar Cases: {stats['valid_cases']}\n"
                f"Favorable Precedents: {int(stats['favorable_count'])}\n"
            )

            prompt = (
                f"User Facts: {user_facts}\n\n"
                f"Statistical Context:\n{stats_context}\n\n"
                f"Top 3 Similar Precedents:\n{case_summaries}\n"
                f"Instruction: Explain the viability score. If the top cases contradict the low/high score, explain why the broader trend matters."
            )
            
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=STRATEGIC_ANALYSIS_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            )
            return response.content.strip()
        except Exception as e:
            return "Unable to generate strategic advice at this time."

    def _calculate_stats(self, outcomes: List[str], user_role: str) -> Dict[str, float]:
        """Step 3: Weighted Scoring Algorithm & Stats"""
        total_weight = 0.0
        valid_cases = 0
        favorable_count = 0
        
        # Normalize role
        user_role = user_role.lower()
        is_petitioner_side = user_role in ["petitioner", "complainant", "appellant"]
        
        for outcome in outcomes:
            outcome = outcome.lower()
            score = 0.0
            
            # Skip unknown
            if outcome in ["unknown", "pending", "disposed"]:
                continue
                
            valid_cases += 1
            
            # Determine "Win" vs "Loss" based on perspective
            is_favorable = False
            is_mixed = "partly" in outcome or "modified" in outcome
            
            if is_petitioner_side:
                if "allowed" in outcome or "convicted" in outcome or "granted" in outcome:
                    is_favorable = True
            else: # Respondent side
                if "dismissed" in outcome or "acquitted" in outcome or "rejected" in outcome:
                    is_favorable = True
            
            # Assign Score & Count
            if is_favorable:
                score = 1.0
                favorable_count += 1
            elif is_mixed:
                score = 0.5
            else:
                score = 0.0
                
            total_weight += score
            
        viability_score = (total_weight / valid_cases * 100) if valid_cases > 0 else 0.0
        
        return {
            "score": viability_score,
            "favorable_count": favorable_count,
            "valid_cases": valid_cases
        }

    async def predict_viability(
        self, 
        raw_facts: str, 
        user_role: str = "Petitioner", 
        court_filter: Optional[str] = None
    ) -> PredictionResult:
        """Main Orchestrator"""
        
        # 1. Preprocessing
        search_query_text = await self._extract_key_facts(raw_facts)
        
        # 2. Retrieval
        filters = {"document_type": "judgment"}
        if court_filter and court_filter != "All Courts":
            filters["metadata.court_name"] = court_filter
            
        query = SearchQuery(
            query=search_query_text,
            top_k=settings.VIABILITY_RETRIEVAL_TOP_K,
            filters=filters
        )
        
        search_response = await hybrid_search_service.search(query)
        
        # LOGGING: Print all retrieved chunks to console
        print(f"\n--- [VIABILITY] Retrieved {len(search_response.results)} Chunks ---")
        for i, res in enumerate(search_response.results):
            meta = res.metadata
            print(f"[{i+1}] Score: {res.score:.4f} | Case: {meta.get('case_title', 'Unknown')} ({meta.get('year_of_judgment', 'N/A')}) | Outcome: {meta.get('outcome', 'N/A')}")
            print(f"    Snippet: {res.text_for_embedding[:150]}...\n")
        print("------------------------------------------------------------\n")
        
        # Filter Results (Min Score & Valid Metadata)
        relevant_cases = []
        seen_cases = set()
        
        for result in search_response.results:
            # Re-verify score threshold just in case
            if result.score < settings.VIABILITY_MIN_SCORE:
                continue
            
            # CASE-LEVEL DEDUPLICATION: Ensure 1 Vote per Case
            case_title = result.metadata.get("case_title", "Unknown")
            if case_title in seen_cases and case_title != "Unknown":
                continue
                
            seen_cases.add(case_title)
            relevant_cases.append(result)
            
        # 3. Scoring
        # Extract outcomes from metadata
        outcomes = [r.metadata.get("outcome", "Unknown") for r in relevant_cases]
        stats = self._calculate_stats(outcomes, user_role)
        viability_score = stats["score"]
        
        # Determine Label
        if viability_score >= (settings.VIABILITY_HIGH_PROB_THRESHOLD * 100):
            label = "High"
        elif viability_score <= (settings.VIABILITY_LOW_PROB_THRESHOLD * 100):
            label = "Low"
        else:
            label = "Medium"
            
        # 4. Strategic Insight
        # Convert SearchResult objects to dicts for the helper
        top_case_dicts = [
            {
                "metadata": r.metadata,
                "score": r.score,
                "text_for_embedding": r.text_for_embedding
            }
            for r in relevant_cases
        ]
        
        advice = await self._generate_advice(search_query_text, top_case_dicts, stats)
        
        # 5. Format Output
        # Return top 5 precedents for UI display
        display_precedents = []
        for r in relevant_cases[:5]:
             display_precedents.append({
                 "case_title": r.metadata.get("case_title", "Unknown Case"),
                 "court": r.metadata.get("court_name", "Unknown Court"),
                 "year": r.metadata.get("year_of_judgment", ""),
                 "outcome": r.metadata.get("outcome", "Unknown"),
                 "score": r.score,
                 "snippet": r.text_for_embedding[:300] + "...",
                 "pdf_url": r.metadata.get("doc_url", "")
             })

        return PredictionResult(
            viability_score=round(viability_score, 1),
            viability_label=label,
            total_analyzed=len(relevant_cases),
            favorable_count=stats["favorable_count"],
            top_precedents=display_precedents,
            strategic_advice=advice
        )

viability_service = ViabilityService()
