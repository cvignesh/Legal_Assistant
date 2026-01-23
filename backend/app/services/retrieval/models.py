"""
Pydantic models for hybrid search retrieval
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SearchQuery(BaseModel):
    """Input query for hybrid search"""
    query: str = Field(..., description="User's search query")
    top_k: int = Field(default=10, description="Number of final results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="MongoDB filters")
    
    # Optional: Filter by document type
    document_type: Optional[Literal["act", "judgment"]] = None
    
    # Optional: Year range for judgments
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class SearchResult(BaseModel):
    """A single search result chunk"""
    chunk_id: str
    score: float
    text_for_embedding: str
    document_type: str
    
    # Optional fields depending on document type
    metadata: Dict[str, Any]
    
    # Source tracking
    source: str = Field(description="Source: vector, keyword, or hybrid")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "BNS_Sec_420",
                "score": 0.95,
                "text_for_embedding": "Section 420: Cheating...",
                "document_type": "act",
                "metadata": {
                    "act_name": "Bharatiya Nyaya Sanhita 2023",
                    "section_id": "420"
                },
                "source": "hybrid"
            }
        }


class SearchResponse(BaseModel):
    """Response from hybrid search"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float
    
    # Pipeline metadata
    vector_results_count: int = 0
    keyword_results_count: int = 0
    after_dedup_count: int = 0
    after_rerank_count: int = 0


class RerankRequest(BaseModel):
    """Request for reranking"""
    query: str
    documents: List[Dict[str, Any]]
    top_n: int = 10
