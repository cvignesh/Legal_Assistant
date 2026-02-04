"""
Argument-aware retrieval for Legal Argument Miner
"""

from typing import List, Dict
import logging
import json
from app.services.retrieval.vector_search import vector_search

logger = logging.getLogger(__name__)

# Mapping logical roles → your chunk metadata
ROLE_TO_FILTER = {
    "prosecution": {
        "metadata.section_type": "Submission_Respondent"
    },
    "defense": {
        "metadata.section_type": "Submission_Petitioner"
    }
}

ARGUMENT_QUERY_HINT = (
    "arguments advanced legal submissions contentions submissions"
)

async def retrieve_arguments(
    *,
    case_id: str,
    role: str,
    top_k: int = 20
) -> List[Dict]:
    """
    Retrieve argument-related chunks for a given role
    
    Args:
        case_id: Case identifier
        role: 'prosecution' | 'defense'
        top_k: Number of chunks to retrieve
        
    Returns:
        List of relevant chunks
    """

    if role not in ROLE_TO_FILTER:
        raise ValueError(f"Invalid role: {role}")

    filters = {
        **ROLE_TO_FILTER[role],
        "metadata.case_number": case_id
    }

    logger.info(f"Retrieving {role} arguments for case_number={case_id} with filters: {filters}")

    results = await vector_search(
        query=ARGUMENT_QUERY_HINT,
        top_k=top_k,
        filters=filters
    )

    logger.info(f"Retrieved {len(results)} chunks for {role}")
    for i, chunk in enumerate(results):
        logger.info(f"  [{i+1}] Chunk ID: {chunk.get('chunk_id', 'N/A')} | Score: {chunk.get('score', 'N/A')}")
        logger.info(f"      Section Type: {chunk.get('metadata', {}).get('section_type', 'N/A')}")
        logger.info(f"      Raw Content (first 200 chars): {chunk.get('raw_content', '')[:200]}")
        logger.info(f"      Text for Embedding (first 200 chars): {chunk.get('text_for_embedding', '')[:200]}")
