from typing import List, Dict
import logging
import asyncio
from app.services.chat.chat_service import chat_service

logger = logging.getLogger(__name__)

# ----------------------------------------
# CONFIGURATION (safe defaults)
# ----------------------------------------
MAX_CONCURRENT_REQUESTS = 8
MAX_RETRIES = 2
BATCH_SIZE = 4

NORMALIZATION_PROMPT = """
You are a senior legal analyst extracting ONLY substantive legal arguments.

STRICT RULES:

A legal argument MUST:
- Contain a contention, challenge, defence, or justification
- Assert a legal defect, illegality, procedural lapse, or reasoning
- State why an action/order is valid or invalid

DO NOT extract:
- narration of proceedings
- "counsel submitted", "drew attention", "pointed out"
- references to paragraphs or documents without a legal contention
- court observations
- background facts
- relief/prayer requests

DO NOT generate fallback statements like:
"No legal arguments exist"

Return only real legal arguments as short bullet points.

If no legal argument exists in the text:
RETURN NOTHING.

TEXT:
{content}
"""


async def _normalize_single_chunk(chunk: Dict, index: int, semaphore: asyncio.Semaphore):
    async with semaphore:
        content = chunk.get("raw_content") or chunk.get("supporting_quote", "")

        if not content or not content.strip():
            logger.warning(f"Skipping empty chunk at index {index}")
            return []

        logger.info(f"Normalizing chunk {index}")
        logger.debug(f"[NORMALIZER] Chunk {index} input (first 250 chars): {content[:250]}")

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await chat_service.llm.apredict(
                    NORMALIZATION_PROMPT.format(content=content.strip())
                )

                logger.debug(f"[NORMALIZER] Chunk {index} output: {response[:250]}")

                arguments = [
                    line.strip("-• ").strip()
                    for line in response.split("\n")
                    if line.strip()
                ]

                return arguments

            except Exception as e:
                logger.warning(
                    f"Retry {attempt+1}/{MAX_RETRIES} failed for chunk {index}: {e}"
                )
                await asyncio.sleep(1)

        logger.error(f"Failed to normalize chunk {index} after retries")
        return []


def _chunk_batches(chunks, size):
    for i in range(0, len(chunks), size):
        yield chunks[i:i + size]

async def normalize_arguments(chunks: List[Dict]) -> List[str]:

    if not chunks:
        logger.warning("No chunks provided to normalize_arguments")
        return []

    logger.info(f"Normalizing {len(chunks)} chunks (BATCH MODE)")

    batches = list(_chunk_batches(chunks, BATCH_SIZE))

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def process_batch(batch, batch_index):

        async with semaphore:

            combined_text = "\n\n---\n\n".join(
                (c.get("raw_content") or c.get("supporting_quote", "")).strip()
                for c in batch
                if c.get("raw_content") or c.get("supporting_quote")
            )

            if not combined_text:
                return []

            for attempt in range(MAX_RETRIES + 1):

                try:

                    response = await chat_service.llm.apredict(
                        NORMALIZATION_PROMPT.format(content=combined_text)
                    )

                    arguments = [
                        line.strip("-• ").strip()
                        for line in response.split("\n")
                        if line.strip()
                    ]

                    return arguments

                except Exception as e:
                    logger.warning(
                        f"Retry {attempt+1}/{MAX_RETRIES} failed for batch {batch_index}: {e}"
                    )
                    await asyncio.sleep(1)

            return []

    tasks = [
        process_batch(batch, i+1)
        for i, batch in enumerate(batches)
    ]

    results = await asyncio.gather(*tasks)

    extracted_arguments = [
        arg
        for sublist in results
        for arg in sublist
    ]

    # Dedup
    seen = set()
    deduped = []

    for arg in extracted_arguments:
        key = arg.lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(arg)

    logger.info(f"Extracted {len(deduped)} normalized arguments")

    return deduped

    """
    Parallel chunk-wise normalization with concurrency control.
    """

    if not chunks:
        logger.warning("No chunks provided to normalize_arguments")
        return []

    logger.info(f"Normalizing {len(chunks)} chunks (parallel mode)")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    tasks = [
        _normalize_single_chunk(chunk, idx + 1, semaphore)
        for idx, chunk in enumerate(chunks)
    ]

    results = await asyncio.gather(*tasks)

    # Flatten results
    extracted_arguments = [
        arg
        for sublist in results
        for arg in sublist
    ]

    # Deduplicate (case-insensitive)
    seen = set()
    deduped_arguments = []

    for arg in extracted_arguments:
        key = arg.lower()
        if key and key not in seen:
            deduped_arguments.append(arg)
            seen.add(key)

    logger.info(f"Extracted {len(deduped_arguments)} unique normalized arguments")

    for i, arg in enumerate(deduped_arguments):
        logger.info(f"  Arg {i+1}: {arg[:100]}")

    return deduped_arguments
