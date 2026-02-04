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

    logger.info(f"Normalizing {len(chunks)} chunks (batch mode)")
    # Concatenate all chunk contents for batch LLM call
    contents = []
    for i, chunk in enumerate(chunks):
        content = chunk.get("raw_content") or chunk.get("supporting_quote", "")
        if content.strip():
            contents.append(content.strip())
    if not contents:
        logger.warning("No valid content in chunks for normalization")
        return []
    batch_text = "\n\n".join(contents)
    print(f"\n[NORMALIZER] Input to LLM (first 500 chars):\n{batch_text[:500]}")
    response = await chat_service.llm.apredict(NORMALIZATION_PROMPT.format(content=batch_text))
    print(f"\n[NORMALIZER] LLM output (first 500 chars):\n{response[:500]}")
    arguments = [
        line.strip("-• ").strip()
        for line in response.split("\n")
        if line.strip()
    ]
    # Deduplicate arguments (case-insensitive)
    seen = set()
    deduped_arguments = []
    for arg in arguments:
        key = arg.lower()
        if key and key not in seen:
            deduped_arguments.append(arg)
            seen.add(key)
    logger.info(f"Extracted {len(deduped_arguments)} unique normalized arguments")
    for i, arg in enumerate(deduped_arguments):
        logger.info(f"  Arg {i+1}: {arg[:100]}")
    return deduped_arguments
