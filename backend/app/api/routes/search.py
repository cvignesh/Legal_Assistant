"""
Search API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.retrieval.models import SearchQuery, SearchResponse
from app.services.retrieval.hybrid_search import hybrid_search_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    query: SearchQuery
):
    """
    Main hybrid search endpoint
    
    Combines:
    - Vector search (semantic/embedding-based)
    - Keyword search (BM25/text-based)
    - Deduplication (ID or similarity-based)
    - Dual reranking (Cohere → LLM)
    
    Returns ranked results with metadata
    """
    try:
        return await hybrid_search_service.search(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results"),
    document_type: Optional[str] = Query(None, description="Filter by type: act or judgment"),
    year_from: Optional[int] = Query(None, description="Filter judgments from year"),
    year_to: Optional[int] = Query(None, description="Filter judgments to year")
):
    """
    GET version of search endpoint for simple queries
    """
    query = SearchQuery(
        query=q,
        top_k=top_k,
        document_type=document_type,
        year_from=year_from,
        year_to=year_to
    )
    
    try:
        return await hybrid_search_service.search(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
