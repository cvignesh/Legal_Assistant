"""
Chat Service with LangChain RAG and ConversationBufferMemory
"""
from typing import Dict, List
import time
import uuid
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
import os
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.services.chat.retriever import ChatbotRetriever
from app.services.chat.models import ChatRequest, ChatResponse, Citation, GroupedSource
import logging
import httpx

logger = logging.getLogger(__name__)


# In-memory session store
chat_sessions: Dict[str, ConversationBufferMemory] = {}


class ChatService:
    """RAG-based chat service with conversation memory"""
    
    def __init__(self):
        # Initialize LLM based on provider
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openai":
            logger.info(f"Initializing ChatService with OpenAI model: {settings.LLM_MODEL}")
            self.llm = ChatOpenAI(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        elif provider == "groq":
            logger.info(f"Initializing ChatService with Groq model: {settings.LLM_MODEL}")
            self.llm = ChatGroq(
                api_key=settings.LLM_API_KEY,  # Use generic LLM_API_KEY instead of GROQ_API_KEY
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
        
        # Initialize retriever (chatbot-specific with metadata enrichment)
        self.retriever = ChatbotRetriever(top_k=settings.CHAT_RETRIEVAL_TOP_K)
        
        # Guardrails Config
        self.guardrails_url = os.getenv("GUARDRAILS_API_URL", "http://localhost:8001")
        self.enable_guardrails = True # Could be setting
    
    def get_or_create_session(self, session_id: str) -> ConversationBufferMemory:
        """Get existing session or create new one"""
        if session_id not in chat_sessions:
            logger.info(f"Creating new chat session: {session_id}")
            chat_sessions[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        return chat_sessions[session_id]
    
    def clear_session(self, session_id: str):
        """Clear conversation memory for a session"""
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"Cleared chat session: {session_id}")
    
    def create_session_id(self) -> str:
        """Generate a new session ID"""
        return str(uuid.uuid4())
    
    def extract_citations(self, source_documents: List) -> List[Citation]:
        """Extract citations from source documents"""
        citations = []
        
        for doc in source_documents:
            citation = Citation(
                chunk_id=doc.metadata.get("chunk_id", ""),
                score=doc.metadata.get("score", 0.0),
                text=doc.page_content[:300],  # First 300 chars as excerpt
                source=self._format_source_name(doc.metadata),
                metadata=doc.metadata
            )
            citations.append(citation)
        
        return citations
    
    def _format_source_name(self, metadata: Dict) -> str:
        """Format a user-friendly source name from metadata"""
        doc_type = metadata.get("document_type", "")
        
        if doc_type == "act":
            act_name = metadata.get("act_name", "")
            section_id = metadata.get("section_id", "")
            if act_name and section_id:
                return f"{act_name}, Section {section_id}"
            elif act_name:
                return act_name
            elif section_id:
                return f"Section {section_id}"
        
        elif doc_type == "judgment":
            case_title = metadata.get("case_title", "")
            year = metadata.get("year_of_judgment", "")
            if case_title and year:
                return f"{case_title} ({year})"
            elif case_title:
                return case_title
        
        # Fallback to chunk_id or default
        chunk_id = metadata.get("chunk_id", "")
        return chunk_id if chunk_id else "Legal Document"
    
    def group_citations(self, citations: List[Citation]) -> List['GroupedSource']:
        """Group citations by Case/Act"""
        from app.services.chat.models import GroupedSource
        
        groups = {}
        for cit in citations:
            meta = cit.metadata
            doc_type = meta.get("document_type", "unknown")
            
            # Key Construction
            if doc_type == "judgment":
                key = meta.get("case_title") or meta.get("filename") or "Unknown Case"
                year = meta.get("year_of_judgment")
                title = f"{key} ({year})" if year else key
                doc_url = meta.get("doc_url")
            elif doc_type == "act":
                key = meta.get("act_name") or "Unknown Act"
                title = key
                doc_url = None
            else:
                key = "Other Documents"
                title = key
                doc_url = None
                
            if key not in groups:
                groups[key] = {
                    "id": key,
                    "title": title,
                    "doc_url": doc_url,
                    "metadata": meta,
                    "chunks": []
                }
            
            groups[key]["chunks"].append(cit)
            
        return [GroupedSource(**g) for g in groups.values()]

    async def _validate_text(self, text: str, validators: List[Dict], context: List[Dict] = None) -> Dict:
        """Call Guardrails API to validate text"""
        if not self.enable_guardrails:
            return {"passed": True, "validated_text": text, "errors": []}
            
        payload = {
            "text": text,
            "validators": validators,
            "context": context or []
        }
        
        
        logger.info(f"Guardrails Request: Calling validators {[v['name'] for v in validators]}")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.guardrails_url}/validate", json=payload, timeout=60.0)
                resp.raise_for_status()
                result = resp.json()
                logger.info(f"Guardrails Response: {result}")
                return result
        except Exception as e:
            import traceback
            logger.error(f"Guardrails API failed: {e}\n{traceback.format_exc()}")
            # Fail open (allow text) or closed (block) based on policy. Here: fail open but log.
            return {"passed": True, "validated_text": text, "errors": [], "failed_open": True}

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message with RAG and conversation memory
        
        Args:
            request: ChatRequest with session_id and message
            
        Returns:
            ChatResponse with answer and citations
        """
        start_time = time.time()
        
        try:
            # Get or create conversation memory
            memory = self.get_or_create_session(request.session_id)
            
            guardrail_actions = []

            # 1. Input Validation
            input_validators = [
                {"name": "detect_prompt_injection"},
                {"name": "unusual_prompt"}
            ]
            
            input_result = await self._validate_text(request.message, input_validators)
            
            if not input_result.get("passed"):
                # BLOCKING ACTION
                errors = input_result.get("errors", [])
                logger.warning(f"Guardrails blocked input: {errors}")
                
                # Determine specific reason
                blocked_actions = []
                reason_msg = "Your message was flagged as potentially unsafe."
                
                for err in errors:
                    v_name = err.get("validator")
                    if v_name == "detect_prompt_injection":
                        blocked_actions.append("Prompt Injection Blocked")
                        reason_msg = "[Security Alert] Prompt Injection attempt detected."
                    elif v_name == "unusual_prompt":
                        blocked_actions.append("Unusual Prompt Blocked")
                        reason_msg = "[Security Alert] Message flagged as unusual or incoherent."
                    else:
                        blocked_actions.append(f"Safety Violation: {v_name}")

                if not blocked_actions:
                    blocked_actions.append("Safety Violation")
                    reason_msg = f"[Security Alert] Message flagged as unsafe. Reason: {errors}"
                
                return ChatResponse(
                    session_id=request.session_id,
                    answer=reason_msg,
                    citations=[],
                    sources=[],
                    guardrail_actions=blocked_actions,
                    processing_time_ms=0
                )

            
            # Strict RAG Prompt
            from langchain.prompts import PromptTemplate
            
            rag_prompt_template = """
You are a Legal Assistant AI that answers questions strictly based on the provided context.

CONTEXT:
{context}

CHAT HISTORY:
{chat_history}

QUESTION: {question}

GUIDELINES:
1. USE ONLY THE CONTEXT ABOVE. Do not use your internal knowledge.
2. If the answer is not in the context, say "I cannot find information about this in the projected case laws or acts." instructions.
3. CONCISE CITATIONS: When mentioning a case, integrate it naturally (e.g., "In Ananthi vs The District Registrar (2023)..."). Do NOT repeat the full citation at the end of the sentence if you already mentioned it.
4. VERDICTS: State the outcome naturally (e.g., "The court allowed the petition"). Do NOT paste raw metadata strings like "Verdict: Allowed | Winner: Petitioner".
5. Answer directly and professionally.

ANSWER:
"""
            RAG_PROMPT = PromptTemplate(
                template=rag_prompt_template, 
                input_variables=["context", "chat_history", "question"]
            )

            # Create conversational retrieval chain with custom prompt
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=memory,
                return_source_documents=True,
                verbose=True,
                combine_docs_chain_kwargs={"prompt": RAG_PROMPT}
            )
            
            # Invoke chain
            result = await chain.ainvoke({"question": request.message})
            
            # Extract answer and sources
            answer = result.get("answer", "")
            source_docs = result.get("source_documents", [])
            
            # Create citations
            citations = self.extract_citations(source_docs)
            sources = self.group_citations(citations)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # 2. Output Validation
            output_validators = [
                {"name": "grounded_in_context", "parameters": {"threshold": 0.7}}, # Needs context passing if supported by API logic
                {"name": "citations_present"},
                {"name": "detect_pii", "mode": "redact"}
            ]
            
            # Prepare context for grounding check (extract text from source_docs)
            validation_context = [{"id": doc.metadata.get("chunk_id", str(i)), "text": doc.page_content} for i, doc in enumerate(source_docs)]
            
            output_result = await self._validate_text(answer, output_validators, context=validation_context)
            
            final_answer = answer
            
            # Always check if text was modified (e.g. Redacted) even if passed=True
            if output_result.get("validated_text") and output_result.get("validated_text") != answer:
                final_answer = output_result.get("validated_text")
                if "<REDACTED>" in final_answer:
                    guardrail_actions.append("PII Redacted")

            if not output_result.get("passed"):
                errors = output_result.get("errors", [])
                # Log errors but we already handled text replacement
                for err in errors:
                     pass
            
            # If no errors for specific checks, we can add positive badges? 
            # Or just rely on negative ones? 
            # User asked: "PII Redacted, source verified, highly grounded"
            
            # Logic for positive badges involves checking if specific validators passed.
            # But the API only returns errors for failures. 
            # If 'grounded_in_context' is NOT in errors, it passed.
            
            # Add positive badges if checks passed AND API didn't fail open
            if not output_result.get("failed_open"):
                failed_validators = [e.get("validator") for e in output_result.get("errors", [])]
                
                # Grounded check - only if documents exist and we have a pass
                if "grounded_in_context" not in failed_validators and output_result.get("passed") is not None and source_docs:
                    guardrail_actions.append("Verified Grounded")
                
                # Citations check - only if we didn't just give a "Not found" answer AND we strictly have citations
                is_refusal = "cannot find information" in final_answer.lower()
                has_citations = len(citations) > 0 or len(sources) > 0
                if "citations_present" not in failed_validators and output_result.get("passed") is not None and not is_refusal and has_citations:
                    guardrail_actions.append("Citation Present")

            logger.info(f"Chat response generated in {processing_time:.2f}ms with {len(citations)} citations")

            return ChatResponse(
                session_id=request.session_id,
                answer=final_answer,
                citations=citations,
                sources=sources,
                guardrail_actions=guardrail_actions,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise


# Singleton service instance
chat_service = ChatService()
