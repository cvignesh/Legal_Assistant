from typing import List, Tuple
import logging
from app.services.chat.chat_service import chat_service

logger = logging.getLogger(__name__)

POLARITY_PROMPT = """
You are a legal expert classifying arguments in a preventive detention judgment.

Classify each argument into one of these categories:

PROSECUTION_ARGUMENT:
- Arguments made by the State/Respondent/Prosecution about THIS SPECIFIC CASE
- Supports detention OR justifies authority action
- Defends the detention order or government action
- Must reference ACTUAL FACTS of this case (specific accused, specific evidence, specific dates)
- Example: "The accused failed to provide evidence of legitimate income sources"

DEFENSE_ARGUMENT:
- Arguments made by the Petitioner/Defense about THIS SPECIFIC CASE
- Challenges detention OR alleges illegality OR procedural defect
- Attacks the detention order or seeks relief
- Must reference ACTUAL FACTS of this case (specific accused, specific evidence, specific dates)
- Example: "The detention order failed to consider the accused's incarceration in another case"

COURT_OBSERVATION:
- Court's own reasoning, analysis, or findings
- Judicial observations or conclusions
- Court's interpretation of law or facts
- Statements from the judgment/order section (not party submissions)

LEGAL_PRINCIPLE:
- Hypothetical legal illustrations using generic names like "A", "B", "public servant"
- Abstract explanations of abetment, conspiracy, or legal doctrines
- Statements about how Section 107, Section 109, or other laws work IN GENERAL
- Precedent case explanations or legal illustrations
- ANY statement that explains what COULD constitute an offense, not what DID happen
- Statements using phrases like: "can be", "would constitute", "is guilty of", "falls under"
- Generic legal concepts without specific case facts

CRITICAL KEYWORD PATTERNS FOR LEGAL_PRINCIPLE:
- Contains "A", "B", or generic placeholder names (not actual accused names)
- Mentions "abetment by instigation", "Thirdly clause", "Section 107", "Section 109" as abstract concepts
- Uses conditional language: "can constitute", "would amount to", "is liable for"
- Explains what "constitutes" an offense without naming the actual accused
- Describes legal categories abstractly: "A's actions constitute...", "A's guilt is established..."

NOT_A_LEGAL_ARGUMENT:
- Procedural text, narration, relief/prayer, or neutral explanation
- Background facts without legal contention

STRICT CLASSIFICATION RULES:
1. If it uses generic names like "A" or "public servant" → LEGAL_PRINCIPLE
2. If it explains what "constitutes" abetment/offense abstractly → LEGAL_PRINCIPLE  
3. If it mentions "Section 107" or "Thirdly clause" as legal doctrine → LEGAL_PRINCIPLE
4. If it says "X's actions constitute Y" without naming actual accused → LEGAL_PRINCIPLE
5. If it references SPECIFIC accused by name + SPECIFIC facts → PROSECUTION/DEFENSE_ARGUMENT

EXAMPLES:
- "A's actions constitute abetment by instigation" → LEGAL_PRINCIPLE (generic "A")
- "P. Nallammal's actions constitute abetment" → PROSECUTION_ARGUMENT (specific accused)
- "The public servant's request to keep wealth constitutes abetment" → LEGAL_PRINCIPLE (generic concept)
- "The accused's request to keep wealth in her name was improper" → PROSECUTION_ARGUMENT (specific case)
- "A's guilt is established under the Thirdly clause" → LEGAL_PRINCIPLE (abstract legal doctrine)
- "The accused is guilty under Section 13(1)(e)" → PROSECUTION_ARGUMENT (specific charge)

Return STRICT JSON list:
[
  {{"argument": "...", "role": "PROSECUTION_ARGUMENT"}},
  {{"argument": "...", "role": "DEFENSE_ARGUMENT"}},
  {{"argument": "...", "role": "COURT_OBSERVATION"}},
  {{"argument": "...", "role": "LEGAL_PRINCIPLE"}}
]

DO NOT add new arguments.
DO NOT summarize.
DO NOT explain.

ARGUMENTS:
{arguments}
"""


async def classify_argument_polarity(arguments: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classifies arguments into prosecution and defense categories.
    Filters out court observations, legal principles, and non-legal arguments.
    
    Returns:
        Tuple of (prosecution_arguments, defense_arguments)
    """

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
            
            elif role == "COURT_OBSERVATION":
                # Filter out court observations - log but don't include
                logger.info(f"[POLARITY] Filtered COURT_OBSERVATION: {arg[:100]}...")
                continue
            
            elif role == "LEGAL_PRINCIPLE":
                # Filter out legal principles/illustrations - log but don't include
                logger.info(f"[POLARITY] Filtered LEGAL_PRINCIPLE: {arg[:100]}...")
                continue
            
            # NOT_A_LEGAL_ARGUMENT is also filtered out

        logger.info(f"[POLARITY] Classification complete: {len(prosecution)} prosecution, {len(defense)} defense")

        return prosecution, defense

    except Exception as e:
        logger.error(f"Polarity classification failed: {e}", exc_info=True)
        return [], []
