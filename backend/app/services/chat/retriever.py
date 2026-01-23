"""
Custom LangChain retriever using hybrid search
"""
from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from app.services.retrieval.hybrid_search import hybrid_search_service
from app.services.retrieval.models import SearchQuery
import logging

logger = logging.getLogger(__name__)


class ChatbotRetriever(BaseRetriever):
    """
    Custom retriever for RAG chatbot use case.
    
    Enriches retrieved chunks with metadata headers (Verdict, Winner, Court for Judgments;
    Act Name, Section for Acts) so the LLM can answer questions about case outcomes and legal context.
    
    For other use cases (Viability Predictor, Argument Miner, Clause Search), 
    create separate retriever classes with appropriate metadata injection strategies.
    """
    
    top_k: int = 5
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        """Synchronous retrieval - not used in async context"""
        raise NotImplementedError("Use async version")
    
    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        """Asynchronous retrieval using hybrid search"""
        try:
            # Use hybrid search service
            search_query = SearchQuery(query=query, top_k=self.top_k)
            search_response = await hybrid_search_service.search(search_query)
            
            # Convert search results to LangChain Documents
            documents = []
            for result in search_response.results:
                # Start with original content
                page_content = result.text_for_embedding
                
                # INJECT METADATA INTO CONTEXT (Safe handling of null values)
                doc_type = result.document_type
                
                if doc_type == "judgment":
                    # Helper to safely format metadata values
                    def fmt(value):
                        if value is None or value == "":
                            return "Not specified"
                        if value == "Unknown":
                            return "Unknown"
                        if value == "None":  # Enum default (e.g., WinningParty.NONE)
                            return "Not applicable"
                        return str(value)
                    
                    # Build metadata header for judgments
                    case_title = fmt(result.metadata.get('case_title'))
                    court_name = fmt(result.metadata.get('court_name'))
                    year = fmt(result.metadata.get('year_of_judgment'))
                    outcome = fmt(result.metadata.get('outcome'))
                    winner = fmt(result.metadata.get('winning_party'))
                    section_type = fmt(result.metadata.get('section_type'))
                    party_role = fmt(result.metadata.get('party_role'))
                    
                    meta_header = (
                        f"[CASE CONTEXT]\n"
                        f"Case: {case_title}\n"
                        f"Court: {court_name} ({year})\n"
                        f"Verdict: {outcome} | Winner: {winner}\n"
                        f"Content Type: {section_type} | Party: {party_role}\n"
                        f"---\n"
                    )
                    
                    page_content = meta_header + page_content
                    
                elif doc_type == "act":
                    # Helper to safely format metadata values
                    def fmt(value):
                        if value is None or value == "":
                            return "Not specified"
                        return str(value)
                    
                    # Build metadata header for acts
                    act_name = fmt(result.metadata.get('act_name'))
                    section_id = fmt(result.metadata.get('section_id'))
                    section_title = fmt(result.metadata.get('section_title'))
                    
                    meta_header = (
                        f"[LEGAL ACT]\n"
                        f"Act: {act_name}\n"
                        f"Section: {section_id} - {section_title}\n"
                        f"---\n"
                    )
                    
                    page_content = meta_header + page_content

                # Create LangChain Document
                doc = Document(
                    page_content=page_content,
                    metadata={
                        "chunk_id": result.chunk_id,
                        "score": result.score,
                        "document_type": result.document_type,
                        "source": result.source,
                        **result.metadata
                    }
                )
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            
            # Debug: Log first enriched document (for verification)
            if documents:
                logger.debug(f"Sample enriched content:\n{documents[0].page_content[:500]}...")
            
            return documents
            
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            return []
