"""
MongoDB Atlas Vector Search using $vectorSearch aggregation
"""
from typing import List, Dict, Any, Optional
from app.db.mongo import mongo
from app.core.config import settings
from app.services.embedder import embedder_service
import logging

logger = logging.getLogger(__name__)


async def vector_search(
    query: str,
    top_k: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    min_score: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Perform vector search using MongoDB Atlas Vector Search
    
    Args:
        query: User's search query
        top_k: Number of results to return
        filters: MongoDB filter conditions
        min_score: Minimum similarity score threshold
        
    Returns:
        List of matching chunks with scores
    """
    try:
        # Generate query embedding using embed_batch with single query
        embeddings = await embedder_service.embed_batch([query])
        query_embedding = embeddings[0]  # Get the first (and only) embedding
        
        if min_score is None:
            min_score = settings.VECTOR_MIN_SCORE
        
        # Build $vectorSearch pipeline
        vector_search_stage = {
            "$vectorSearch": {
                "index": settings.VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": top_k * 10,  # Overrequest for better recall
                "limit": top_k
            }
        }
        
        # Add filters if provided
        if filters:
            vector_search_stage["$vectorSearch"]["filter"] = filters
        
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
                "score": {"$meta": "vectorSearchScore"}
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
        pipeline = [vector_search_stage, project_stage, match_stage]
        
        results = []
        async for doc in collection.aggregate(pipeline):
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        logger.info(f"Vector search returned {len(results)} results for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.error(f"Vector search error: {str(e)}")
        raise
