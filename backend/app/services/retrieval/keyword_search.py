"""
MongoDB Atlas Text Search using $search aggregation
"""
from typing import List, Dict, Any, Optional
from app.db.mongo import mongo
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def keyword_search(
    query: str,
    top_k: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    min_score: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Perform keyword/full-text search using MongoDB Atlas Search
    
    Args:
        query: User's search query
        top_k: Number of results to return
        filters: MongoDB filter conditions
        min_score: Minimum relevance score threshold
        
    Returns:
        List of matching chunks with scores
    """
    try:
        if min_score is None:
            min_score = settings.KEYWORD_MIN_SCORE
        
        # Build $search pipeline
        search_stage = {
            "$search": {
                "index": settings.TEXT_INDEX_NAME,
                "text": {
                    "query": query,
                    "path": ["text_for_embedding", "raw_content", "supporting_quote"]
                }
            }
        }
        
        # Add filters using compound search if provided
        if filters:
            search_stage["$search"] = {
                "index": settings.TEXT_INDEX_NAME,
                "compound": {
                    "must": [{
                        "text": {
                            "query": query,
                            "path": ["text_for_embedding", "raw_content", "supporting_quote"]
                        }
                    }],
                    "filter": list(filters.items()) if isinstance(filters, dict) else filters
                }
            }
        
        # Limit results
        limit_stage = {"$limit": top_k}
        
        # Add score projection
        project_stage = {
            "$project": {
                "chunk_id": 1,
                "text_for_embedding": 1,
                "raw_content": 1,
                "supporting_quote": 1,
                "document_type": 1,
                "metadata": 1,
                "created_at": 1,
                "score": {"$meta": "searchScore"}
            }
        }
        
        # Filter by minimum score
        match_stage = {
            "$match": {
                "score": {"$gte": min_score}
            }
        }
        
        # Execute aggregation pipeline
        collection = mongo.db[settings.MONGO_COLLECTION_CHUNKS]
        pipeline = [search_stage, limit_stage, project_stage, match_stage]
        
        results = []
        async for doc in collection.aggregate(pipeline):
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        logger.info(f"Keyword search returned {len(results)} results for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.error(f"Keyword search error: {str(e)}")
        raise
