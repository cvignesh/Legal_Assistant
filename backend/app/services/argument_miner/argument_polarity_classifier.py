from typing import List, Tuple
import logging
from app.services.chat.chat_service import chat_service

logger = logging.getLogger(__name__)

POLARITY_PROMPT = """
You are a legal expert classifying arguments in a preventive detention judgment.

Classify each argument into one of these:

PROSECUTION_ARGUMENT:
Supports detention OR justifies authority action.

DEFENSE_ARGUMENT:
Challenges detention OR alleges illegality OR procedural defect.

NOT_A_LEGAL_ARGUMENT:
Court reasoning, narration, relief/prayer, procedural text, or neutral explanation.

Return STRICT JSON list:
[
  {{"argument": "...", "role": "PROSECUTION_ARGUMENT"}},
  {{"argument": "...", "role": "DEFENSE_ARGUMENT"}}
]

DO NOT add new arguments.
DO NOT summarize.
DO NOT explain.

ARGUMENTS:
{arguments}
"""


async def classify_argument_polarity(arguments: List[str]) -> Tuple[List[str], List[str]]:

    if not arguments:
        return [], []

    joined = "\n".join(f"- {a}" for a in arguments)

    try:

        response = await chat_service.llm.apredict(
            POLARITY_PROMPT.format(arguments=joined)
        )

        import json

        parsed = json.loads(response)

        prosecution = []
        defense = []

        for item in parsed:

            role = item.get("role")
            arg = item.get("argument")

            if not arg:
                continue

            if role == "PROSECUTION_ARGUMENT":
                prosecution.append(arg)

            elif role == "DEFENSE_ARGUMENT":
                defense.append(arg)

        return prosecution, defense

    except Exception as e:
        logger.error(f"Polarity classification failed: {e}", exc_info=True)
        return [], []
