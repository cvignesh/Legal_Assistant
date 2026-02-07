from .retriever import retrieve_arguments
from .normalizer import normalize_arguments
from .argument_polarity_classifier import classify_argument_polarity
from difflib import SequenceMatcher
import logging
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load once globally (VERY IMPORTANT for performance)
_semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
logger = logging.getLogger(__name__)


# --------------------------------------------------
# Post-Normalization Noise Filter
# --------------------------------------------------
def _filter_noise(arguments):

    if not arguments:
        return []

    noise_patterns = [
        r"\bprays?\b",
        r"\bwrit\b",
        r"\bthis court\b",
        r"\bit is seen\b",
        r"\bit is evident\b",
        r"\bafter considering\b",
        r"\bno legal arguments exist\b",
        r"\bpetition is validly filed\b",
        r"\barticle\s*226\b",
        r"\bdismiss(ed)?\b",
        r"\bpetition is liable\b",
        r"\bpetition should be dismissed\b",
    ]

    cleaned = []

    for arg in arguments:

        lower = arg.lower().strip()

        if any(re.search(p, lower) for p in noise_patterns):
            continue

        # Remove ultra short junk
        if len(lower.split()) < 6:
            continue

        cleaned.append(arg.strip())

    return cleaned


# --------------------------------------------------
# Dedup Safety
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


def _semantic_dedup(arguments, threshold=0.78):
    """
    Removes semantically duplicate legal arguments.
    Optimized to pre-compute all embeddings once.
    """

    if not arguments:
        return []

    unique_args = []
    unique_embeddings = []
    
    # Pre-compute all embeddings once
    all_embeddings = _semantic_model.encode(arguments)

    for idx, arg in enumerate(arguments):
        is_duplicate = False

        # Compare with existing unique embeddings
        for u_embedding in unique_embeddings:
            sim = cosine_similarity(
                [all_embeddings[idx]],
                [u_embedding]
            )[0][0]

            if sim >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_args.append(arg)
            unique_embeddings.append(all_embeddings[idx])

    return unique_args

# --------------------------------------------------
# MAIN CASE MINER
# --------------------------------------------------
async def mine_from_case(case_id: str):

    try:

        logger.info(f"=== Starting case_miner for case_id: {case_id} ===")

        # ----------------------------------
        # Retrieve Chunks
        # ----------------------------------
        prosecution_chunks = await retrieve_arguments(
            case_id=case_id,
            role="prosecution"
        )

        defense_chunks = await retrieve_arguments(
            case_id=case_id,
            role="defense"
        )

        logger.info(f"Prosecution chunks retrieved: {len(prosecution_chunks)}")
        logger.info(f"Defense chunks retrieved: {len(defense_chunks)}")

        # Extract doc_url from first chunk (if available)
        doc_url = None
        if prosecution_chunks and len(prosecution_chunks) > 0:
            doc_url = prosecution_chunks[0].get("metadata", {}).get("doc_url")
        elif defense_chunks and len(defense_chunks) > 0:
            doc_url = defense_chunks[0].get("metadata", {}).get("doc_url")

        # ----------------------------------
        # Normalize FIRST (NO ROLE FILTER)
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

        prosecution_args, defense_args = await classify_argument_polarity(
            combined_arguments
        )

        # ----------------------------------
        # Clean + Dedup
        # ----------------------------------
        #prosecution_args = _dedup(_filter_noise(prosecution_args))
        #defense_args = _dedup(_filter_noise(defense_args))
        prosecution_args = _semantic_dedup(_filter_noise(prosecution_args))
        defense_args = _semantic_dedup(_filter_noise(defense_args))

        logger.info(
            f"Final arguments → Prosecution: {len(prosecution_args)}, "
            f"Defense: {len(defense_args)}"
        )

        logger.info("=== Completed case_miner ===")

        return {
            "prosecution": prosecution_args or [],
            "defense": defense_args or [],
            "doc_url": doc_url,
        }

    except Exception as e:
        logger.error(f"Error mining case {case_id}: {e}", exc_info=True)
        return {
            "prosecution": [],
            "defense": [],
            "doc_url": None,
        }
