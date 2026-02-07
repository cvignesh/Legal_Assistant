from typing import Dict, Any
import logging
import asyncio

from .retriever import retrieve_arguments
from .normalizer import normalize_arguments
from .evaluator import evaluate_winner
from .confidence import compute_confidence

from .fact_miner import mine_arguments_from_facts
from .case_miner import mine_from_case
from .hybrid_miner import merge_case_and_facts
from .llm_validator import validate_argument_with_llm

logger = logging.getLogger(__name__)


async def run_argument_miner(
    case_id: str | None = None,
    facts: str | None = None,
    mode: str = "case"
) -> Dict[str, Any]:
    """
    Orchestrator for the Argument Miner feature.

    Returns a dict matching the API schema:
    {
      "prosecution_arguments": [...],
      "defense_arguments": [...],
      "winning_argument": {"reasoning": str, "confidence": int}
    }
    """

    # Validate mode
    if mode not in ("case", "facts"):
        raise ValueError("Invalid mode for argument miner")

    try:
        if mode == "case":
            if not case_id:
                raise ValueError("case_id is required for case mode")
            args = await mine_from_case(case_id)

        elif mode == "facts":
            if not facts:
                raise ValueError("facts are required for facts mode")
            args = await mine_arguments_from_facts(facts)

        # Safety check: ensure args is a dict
        if not args or not isinstance(args, dict):
            logger.error(f"Miner returned invalid result: {args}")
            args = {"prosecution": [], "defense": []}


        # Ensure keys exist
        prosecution_args = args.get("prosecution", [])
        defense_args = args.get("defense", [])

        # LLM-based validation (async parallel processing)
        async def filter_valid_arguments(arguments, context, role_name):
            if not arguments:
                return []
            
            # Validate all arguments in parallel
            validation_tasks = [
                validate_argument_with_llm(arg, context) 
                for arg in arguments
            ]
            validation_results = await asyncio.gather(*validation_tasks)
            
            # Filter and log results
            results = []
            for arg, is_valid in zip(arguments, validation_results):
                logger.info(f"[LLM VALIDATION][{role_name}] Argument: {arg[:100]}... => {'VALID' if is_valid else 'INVALID'}")
                if is_valid:
                    results.append(arg)
            return results

        # Use facts as context if available, else empty string
        context = facts or ""
        prosecution_args = await filter_valid_arguments(prosecution_args, context, "Prosecution")
        defense_args = await filter_valid_arguments(defense_args, context, "Defense")

        # Evaluate winner
        reasoning = await evaluate_winner(prosecution_args, defense_args)
        confidence = compute_confidence(prosecution_args, defense_args)

        # Get doc_url from miner result (available in both case and facts modes)
        doc_url = args.get("doc_url")

        return {
            "prosecution_arguments": prosecution_args,
            "defense_arguments": defense_args,
            "winning_argument": {
                "reasoning": reasoning,
                "confidence": int(confidence)
            },
            "doc_url": doc_url,
            "case_id": case_id if mode == "case" else None
        }

    except Exception as e:
        logger.exception("Argument miner failed")
        raise
