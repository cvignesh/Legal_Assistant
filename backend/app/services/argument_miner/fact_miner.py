from app.services.retrieval.vector_search import vector_search
from .normalizer import normalize_arguments
from .argument_polarity_classifier import classify_argument_polarity
from difflib import SequenceMatcher
import logging
import re

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Noise Filtering (Post Normalization Safety Layer)
# --------------------------------------------------
def _filter_noise(arguments):

    if not arguments:
        return []

    noise_patterns = [
        r"\bprays?\b",
        r"\bseeks?\b",
        r"\bwrit\b",
        r"\bthis court\b",
        r"\bit is seen\b",
        r"\bit is evident\b",
        r"\bafter considering\b",
        r"\bdetention order was passed\b",
        r"\bno legal arguments exist\b",
        r"\bno arguments found\b",
        r"\binsufficient legal\b",
        r"\bpetition is validly filed\b",
        r"\bdismiss(ed)?\b"
        r"\bpetition is liable\b"
        r"\barticle\s*226\b",
        r"\bpetition should be dismissed\b",
    ]

    filtered = []

    for arg in arguments:

        if not arg:
            continue

        lower = arg.lower().strip()

        if len(lower.split()) < 6:
            continue

        if any(re.search(p, lower) for p in noise_patterns):
            continue

        filtered.append(arg.strip())

    return filtered


    if not arguments:
        return []

    noise_patterns = [
        r"\bprays?\b",
        r"\bseeks?\b",
        r"\bwrit\b",
        r"\bthis court\b",
        r"\bit is seen\b",
        r"\bit is evident\b",
        r"\bafter considering\b",
        r"\bdetention order was passed\b",
    ]

    filtered = []

    for arg in arguments:

        if not arg or len(arg.strip()) < 15:
            continue

        lower = arg.lower()

        if any(re.search(p, lower) for p in noise_patterns):
            continue

        filtered.append(arg.strip())

    return filtered


# --------------------------------------------------
# Extra Deduplication Safety
# --------------------------------------------------

def _similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _dedup(arguments, threshold=0.78):

    result = []

    for arg in arguments:

        duplicate = False

        for existing in result:
            if _similar(arg, existing) > threshold:
                duplicate = True
                break

        if not duplicate:
            result.append(arg)

    return result

# --------------------------------------------------
# MAIN FACT MINER
# --------------------------------------------------
async def mine_arguments_from_facts(facts: str):

    if not facts or not facts.strip():
        logger.warning("Empty facts provided to fact_miner")
        return {"prosecution": [], "defense": []}

    logger.info(f"=== Starting fact_miner for facts: {facts[:100]} ===")

    try:

        # ----------------------------------
        # Retrieve Prosecution Chunks
        # ----------------------------------
        prosecution_filters = {
            "metadata.section_type": "Submission_Respondent",
            "document_type": "judgment",
        }

        prosecution_chunks = await vector_search(
            query=facts,
            top_k=10,
            filters=prosecution_filters,
        )

        logger.info(f"Retrieved {len(prosecution_chunks)} prosecution chunks")

        # ----------------------------------
        # Retrieve Defense Chunks
        # ----------------------------------
        defense_filters = {
            "metadata.section_type": "Submission_Petitioner",
            "document_type": "judgment",
        }

        defense_chunks = await vector_search(
            query=facts,
            top_k=10,
            filters=defense_filters,
        )

        logger.info(f"Retrieved {len(defense_chunks)} defense chunks")

        # ----------------------------------
        # Normalize FIRST (NO ROLE FILTER HERE)
        # ----------------------------------
        logger.info("Normalizing prosecution chunks...")
        prosecution_norm = await normalize_arguments(prosecution_chunks)

        logger.info("Normalizing defense chunks...")
        defense_norm = await normalize_arguments(defense_chunks)

        # ----------------------------------
        # Combine + Semantic Role Classification
        # ----------------------------------
        combined_arguments = []

        if prosecution_norm:
            combined_arguments.extend(prosecution_norm)

        if defense_norm:
            combined_arguments.extend(defense_norm)

        logger.info(
            f"Running semantic role classification on {len(combined_arguments)} arguments"
        )

        prosecution_args, defense_args = await classify_argument_polarity(combined_arguments)

        # ----------------------------------
        # Post Processing
        # ----------------------------------
        prosecution_args = _dedup(_filter_noise(prosecution_args))
        defense_args = _dedup(_filter_noise(defense_args))

        logger.info(
            f"Final arguments → Prosecution: {len(prosecution_args)}, "
            f"Defense: {len(defense_args)}"
        )

        logger.info("=== Completed fact_miner ===")

        return {
            "prosecution": prosecution_args,
            "defense": defense_args,
        }

    except Exception as e:
        logger.error(f"Error mining arguments: {e}", exc_info=True)
        return {"prosecution": [], "defense": []}
