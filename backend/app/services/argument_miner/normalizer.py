from typing import List, Dict
import logging
from app.services.chat.chat_service import chat_service

logger = logging.getLogger(__name__)

NORMALIZATION_PROMPT = """
You are a legal expert.

From the text below, extract ONLY the legal arguments advanced by the party.
- Return each argument as a short bullet point
- Ignore court observations, findings, or conclusions
- Do NOT add new arguments
- Be faithful to the text

TEXT:
{content}
"""

async def normalize_arguments(chunks: List[Dict]) -> List[str]:
    """
    Convert raw retrieved chunks into clean legal arguments
    """
    if not chunks:
        logger.warning("No chunks provided to normalize_arguments")
        return []

    logger.info(f"Normalizing {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        content = chunk.get("raw_content") or chunk.get("supporting_quote", "")
        logger.debug(f"  Chunk {i+1} content (first 150 chars): {content[:150]}")


    text = "\n\n".join(
        c.get("raw_content") or c.get("supporting_quote", "")
        for c in chunks
    )

    print("\n[NORMALIZER] Full input to LLM:\n" + text)

    response = await chat_service.llm.apredict(
        NORMALIZATION_PROMPT.format(content=text)
    )

    print("\n[NORMALIZER] Full LLM output:\n" + response)

    arguments = [
        line.strip("-• ").strip()
        for line in response.split("\n")
        if line.strip()
    ]

    logger.info(f"Extracted {len(arguments)} normalized arguments")
    for i, arg in enumerate(arguments):
        logger.info(f"  Arg {i+1}: {arg[:100]}")

    return arguments
