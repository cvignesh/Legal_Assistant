from .retriever import retrieve_arguments
from .normalizer import normalize_arguments
import logging

logger = logging.getLogger(__name__)


async def mine_from_case(case_id: str):
    """
    Extract prosecution and defense arguments from a judgment
    using argument-aware retrieval + normalization
    """
    try:
        logger.info(f"=== Starting case_miner for case_id: {case_id} ===")
        
        logger.info(f"Retrieving prosecution chunks...")
        prosecution_chunks = await retrieve_arguments(
            case_id=case_id,
            role="prosecution"
        )
        logger.info(f"Prosecution chunks retrieved: {len(prosecution_chunks) if prosecution_chunks else 0}")

        logger.info(f"Retrieving defense chunks...")
        defense_chunks = await retrieve_arguments(
            case_id=case_id,
            role="defense"
        )
        logger.info(f"Defense chunks retrieved: {len(defense_chunks) if defense_chunks else 0}")

        logger.info(f"Normalizing prosecution arguments...")
        prosecution_args = await normalize_arguments(prosecution_chunks)
        logger.info(f"Prosecution arguments normalized: {len(prosecution_args) if prosecution_args else 0}")

        logger.info(f"Normalizing defense arguments...")
        defense_args = await normalize_arguments(defense_chunks)
        logger.info(f"Defense arguments normalized: {len(defense_args) if defense_args else 0}")

        logger.info(f"=== Completed case_miner for case_id: {case_id} ===")

        return {
            "prosecution": prosecution_args or [],
            "defense": defense_args or []
        }
    except Exception as e:
        logger.error(f"Error mining case {case_id}: {e}", exc_info=True)
        return {
            "prosecution": [],
            "defense": []
        }
