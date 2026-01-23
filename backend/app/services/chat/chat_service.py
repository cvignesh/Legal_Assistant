"""
Chat Service with LangChain RAG and ConversationBufferMemory
"""
from typing import Dict, List
import time
import uuid
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
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
        # Initialize LLM
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )
        
        # Initialize retriever (chatbot-specific with metadata enrichment)
        self.retriever = ChatbotRetriever(top_k=5)
    
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
            
            # Create conversational retrieval chain
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=memory,
                return_source_documents=True,
                verbose=True
            )
            
            # Invoke chain
            result = await chain.ainvoke({"question": request.message})
            
            # Extract answer and sources
            answer = result.get("answer", "")
            source_docs = result.get("source_documents", [])
            
            # Create citations
            citations = self.extract_citations(source_docs)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"Chat response generated in {processing_time:.2f}ms with {len(citations)} citations")
            
            return ChatResponse(
                session_id=request.session_id,
                answer=answer,
                citations=citations,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise


# Singleton service instance
chat_service = ChatService()
