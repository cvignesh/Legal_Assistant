from typing import List
from app.services.chat.chat_service import chat_service

EVALUATION_PROMPT = """
You are a senior judge.

Below are the arguments of both sides.
Compare their legal strength based ONLY on these arguments.

Prosecution Arguments:
{prosecution}

Defense Arguments:
{defense}

Answer in 3–4 sentences:
1. Which side is legally stronger
2. Why
"""

async def evaluate_winner(
    prosecution_args: List[str],
    defense_args: List[str]
) -> str:

    return await chat_service.llm.apredict(
        EVALUATION_PROMPT.format(
            prosecution="\n".join(prosecution_args),
            defense="\n".join(defense_args)
        )
    )
