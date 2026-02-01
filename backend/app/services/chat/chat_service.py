"""
Chat Service with LangChain RAG and ConversationBufferMemory
"""
from typing import Dict, List
import time
import uuid
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.services.chat.retriever import ChatbotRetriever
from app.services.chat.models import ChatRequest, ChatResponse, Citation
import logging

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
            
            logger.info(f"Chat response generated in {processing_time:.2f}ms with {len(citations)} citations")
            
            return ChatResponse(
                session_id=request.session_id,
                answer=answer,
                citations=citations,
                sources=sources,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise


# Singleton service instance
chat_service = ChatService()
