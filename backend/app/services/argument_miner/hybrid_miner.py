from .fact_miner import mine_arguments_from_facts
import logging

logger = logging.getLogger(__name__)


async def merge_case_and_facts(case_args, facts):
    """
    Merge arguments from case retrieval with arguments from facts mining
    """
    if not case_args or not isinstance(case_args, dict):
        logger.warning("case_args is invalid, using empty defaults")
        case_args = {"prosecution": [], "defense": []}

    fact_args = await mine_arguments_from_facts(facts)

    if not fact_args or not isinstance(fact_args, dict):
        logger.warning("fact_args is invalid, using empty defaults")
        fact_args = {"prosecution": [], "defense": []}

    return {
        "prosecution": (case_args.get("prosecution", []) or []) + (fact_args.get("prosecution", []) or []),
        "defense": (case_args.get("defense", []) or []) + (fact_args.get("defense", []) or [])
    }
