"""
Deduplication utilities for search results
"""
from typing import List, Dict, Any
from difflib import SequenceMatcher
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def deduplicate_by_id(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate chunks based on chunk_id
    
    Args:
        chunks: List of search result chunks
        
    Returns:
        Deduplicated list of chunks
    """
    seen_ids = set()
    unique_chunks = []
    
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id") or chunk.get("_id")
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique_chunks.append(chunk)
    
    logger.info(f"ID deduplication: {len(chunks)} → {len(unique_chunks)} chunks")
    return unique_chunks


def deduplicate_by_similarity(
    chunks: List[Dict[str, Any]],
    threshold: float = None
) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate chunks based on text similarity
    
    Args:
        chunks: List of search result chunks
        threshold: Similarity threshold (0.0-1.0), defaults to config value
        
    Returns:
        Deduplicated list of chunks
    """
    if threshold is None:
        threshold = settings.DEDUP_SIMILARITY_THRESHOLD
    
    unique_chunks = []
    
    for chunk in chunks:
        chunk_text = chunk.get("text_for_embedding", "")
        is_duplicate = False
        
        # Check similarity against all existing unique chunks
        for existing in unique_chunks:
            existing_text = existing.get("text_for_embedding", "")
            similarity = SequenceMatcher(None, chunk_text, existing_text).ratio()
            
            if similarity >= threshold:
                # This chunk is too similar to an existing one
                is_duplicate = True
                logger.debug(f"Similarity duplicate found: {similarity:.2f} >= {threshold}")
                break
        
        if not is_duplicate:
            unique_chunks.append(chunk)
    
    logger.info(f"Similarity deduplication: {len(chunks)} → {len(unique_chunks)} chunks")
    return unique_chunks


def deduplicate(
    chunks: List[Dict[str, Any]],
    method: str = None
) -> List[Dict[str, Any]]:
    """
    Deduplicate search results based on configured method
    
    Args:
        chunks: List of search result chunks
        method: Deduplication method ("id", "similarity", "both")
                Defaults to settings.DEDUP_METHOD
        
    Returns:
        Deduplicated list of chunks
    """
    if method is None:
        method = settings.DEDUP_METHOD
    
    if method == "id":
        return deduplicate_by_id(chunks)
    
    elif method == "similarity":
        return deduplicate_by_similarity(chunks)
    
    elif method == "both":
        # First remove exact ID duplicates, then similar ones
        chunks = deduplicate_by_id(chunks)
        chunks = deduplicate_by_similarity(chunks)
        return chunks
    
    else:
        logger.warning(f"Unknown dedup method '{method}', defaulting to 'id'")
        return deduplicate_by_id(chunks)
