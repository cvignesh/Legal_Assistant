from typing import Dict, Any
import logging

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
    if mode not in ("case", "facts", "hybrid"):
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

        else:  # hybrid
            if not case_id or not facts:
                raise ValueError("case_id and facts are required for hybrid mode")
            case_args = await mine_from_case(case_id)
            args = await merge_case_and_facts(case_args, facts)

        # Safety check: ensure args is a dict
        if not args or not isinstance(args, dict):
            logger.error(f"Miner returned invalid result: {args}")
            args = {"prosecution": [], "defense": []}


        # Ensure keys exist
        prosecution_args = args.get("prosecution", [])
        defense_args = args.get("defense", [])

        # LLM-based validation (async filter)
        async def filter_valid_arguments(arguments, context, role_name):
            results = []
            for arg in arguments:
                is_valid = await validate_argument_with_llm(arg, context)
                print(f"[LLM VALIDATION][{role_name}] Argument: {arg[:100]}... => {'VALID' if is_valid else 'INVALID'}")
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

        return {
            "prosecution_arguments": prosecution_args,
            "defense_arguments": defense_args,
            "winning_argument": {
                "reasoning": reasoning,
                "confidence": int(confidence)
            }
        }

    except Exception as e:
        logger.exception("Argument miner failed")
        raise
