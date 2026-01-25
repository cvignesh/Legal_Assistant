"""
Hybrid Search Orchestrator
Combines vector search, keyword search, deduplication, and reranking
"""
from typing import List, Dict, Any, Optional
import time
from app.core.config import settings
from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.keyword_search import keyword_search
from app.services.retrieval.deduplication import deduplicate
from app.services.retrieval.reranking import cohere_rerank, llm_rerank
from app.services.retrieval.models import SearchQuery, SearchResponse, SearchResult
import logging

logger = logging.getLogger(__name__)


def normalize_scores(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize scores to 0-1 range using min-max normalization
    
    Args:
        results: List of results with scores
        
    Returns:
        Results with normalized scores
    """
    if not results:
        return results
    
    scores = [r.get("score", 0.0) for r in results]
    min_score = min(scores)
    max_score = max(scores)
    
    # Avoid division by zero
    if max_score == min_score:
        for r in results:
            r["normalized_score"] = 1.0
        return results
    
    # Min-max normalization
    for r in results:
        original_score = r.get("score", 0.0)
        r["normalized_score"] = (original_score - min_score) / (max_score - min_score)
    
    return results


def merge_and_score(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge vector and keyword search results with weighted score fusion
    
    Args:
        vector_results: Results from vector search
        keyword_results: Results from keyword search
        
    Returns:
        Merged and scored results
    """
    # Normalize scores separately
    vector_results = normalize_scores(vector_results)
    keyword_results = normalize_scores(keyword_results)
    
    # Combine results with score fusion
    combined = {}
    
    # Add vector results with weight
    for result in vector_results:
        chunk_id = result.get("chunk_id")
        result["source"] = "vector"
        combined[chunk_id] = {
            **result,
            "fused_score": result["normalized_score"] * settings.VECTOR_SCORE_WEIGHT
        }
    
    # Add keyword results with weight (or boost if already present)
    for result in keyword_results:
        chunk_id = result.get("chunk_id")
        if chunk_id in combined:
            # Chunk found in both: boost score
            combined[chunk_id]["fused_score"] += result["normalized_score"] * settings.KEYWORD_SCORE_WEIGHT
            combined[chunk_id]["source"] = "hybrid"
        else:
            # New chunk from keyword search only
            result["source"] = "keyword"
            combined[chunk_id] = {
                **result,
                "fused_score": result["normalized_score"] * settings.KEYWORD_SCORE_WEIGHT
            }
    
    # Convert to list and sort by fused score
    merged_results = list(combined.values())
    merged_results.sort(key=lambda x: x["fused_score"], reverse=True)
    
    # Replace score with fused_score for consistency
    for r in merged_results:
        r["score"] = r["fused_score"]
    
    return merged_results


async def hybrid_search(query: SearchQuery) -> SearchResponse:
    """
    Perform hybrid search combining vector, keyword, dedup, and reranking
    
    Args:
        query: SearchQuery with query string and parameters
        
    Returns:
        SearchResponse with ranked results and metadata
    """
    start_time = time.time()
    
    try:
        # Build MongoDB filters from query parameters
        filters = query.filters or {}
        
        if query.document_type:
            filters["document_type"] = query.document_type
        
        if query.year_from or query.year_to:
            year_filter = {}
            if query.year_from:
                year_filter["$gte"] = query.year_from
            if query.year_to:
                year_filter["$lte"] = query.year_to
            filters["metadata.year_of_judgment"] = year_filter
        
        # Step 1: Parallel retrieval
        logger.info(f"Starting hybrid search for query: {query.query[:50]}...")
        
        vector_results = await vector_search(
            query=query.query,
            top_k=settings.VECTOR_SEARCH_TOP_K,
            filters=filters if filters else None
        )
        
        keyword_results = await keyword_search(
            query=query.query,
            top_k=settings.KEYWORD_SEARCH_TOP_K,
            filters=filters if filters else None
        )
        
        vector_count = len(vector_results)
        keyword_count = len(keyword_results)
        
        # Step 2: Merge and score fusion
        merged_results = merge_and_score(vector_results, keyword_results)
        logger.info(f"Merged: {vector_count} vector + {keyword_count} keyword → {len(merged_results)} total")
        
        # Filter by final hybrid score threshold
        merged_results = [r for r in merged_results if r.get("score", 0.0) >= settings.HYBRID_MIN_SCORE]
        logger.info(f"After hybrid threshold filter: {len(merged_results)} results")
        
        # Step 3: Deduplication
        deduplicated_results = deduplicate(merged_results)
        dedup_count = len(deduplicated_results)
        logger.info(f"After deduplication: {dedup_count} unique chunks")
        
        # Step 4: First reranking - Cohere (fast, broad)
        if settings.USE_COHERE_RERANK and settings.COHERE_API_KEY:
            cohere_reranked = await cohere_rerank(
                query=query.query,
                documents=deduplicated_results,
                top_n=settings.COHERE_RERANK_TOP_N
            )
        else:
            cohere_reranked = deduplicated_results[:settings.COHERE_RERANK_TOP_N]
        
        cohere_count = len(cohere_reranked)
        
        # Step 5: Second reranking - LLM (slow, precise)
        if settings.USE_LLM_RERANK:
            final_results = await llm_rerank(
                query=query.query,
                documents=cohere_reranked,
                top_n=query.top_k
            )
        else:
            final_results = cohere_reranked[:query.top_k]
            
        # Final Filter: Drop results with low reranker scores
        # STRICT SAFETY GATE: Drop anything < 0.01 to prevent zero-score junk
        final_results = [doc for doc in final_results if doc.get("score", 0.0) >= settings.HYBRID_MIN_SCORE or doc.get("score", 0.0) < 0.01]
        # Wait, logical error above. Fix: Keep if score >= threshold AND score > 0.01
        final_results = [
            doc for doc in final_results 
            if doc.get("score", 0.0) >= settings.HYBRID_MIN_SCORE and doc.get("score", 0.0) > 0.01
        ]
        logger.info(f"Final results after reranker filter: {len(final_results)}")
        
        # Convert to SearchResult models
        search_results = []
        for doc in final_results:
            search_results.append(SearchResult(
                chunk_id=doc.get("chunk_id", ""),
                score=doc.get("score", 0.0),
                text_for_embedding=doc.get("text_for_embedding", ""),
                document_type=doc.get("document_type", ""),
                metadata=doc.get("metadata", {}),
                source=doc.get("source", "unknown")
            ))
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Build response
        response = SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=round(processing_time, 2),
            vector_results_count=vector_count,
            keyword_results_count=keyword_count,
            after_dedup_count=dedup_count,
            after_rerank_count=cohere_count
        )
        
        logger.info(f"Hybrid search completed in {processing_time:.2f}ms, returned {len(search_results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Hybrid search error: {str(e)}")
        raise


# Singleton service instance
class HybridSearchService:
    """Hybrid search service with all retrieval pipelines"""
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        """Main search endpoint"""
        return await hybrid_search(query)


hybrid_search_service = HybridSearchService()
