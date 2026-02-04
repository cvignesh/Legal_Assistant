from app.services.retrieval.vector_search import vector_search
import logging

logger = logging.getLogger(__name__)


async def mine_arguments_from_facts(facts: str):
    """
    Retrieve prosecution and defense arguments from Atlas chunks similar to user's facts.
    Uses RAG approach: search for similar judgments and extract arguments from them.
    """
    if not facts or not facts.strip():
        logger.warning("Empty facts provided to fact_miner")
        return {"prosecution": [], "defense": []}

    logger.info(f"=== Starting fact_miner for facts: {facts[:100]}... ===")

    try:
        prosecution_args = []
        defense_args = []

        # Search for prosecution arguments (Submission_Respondent)
        prosecution_filters = {
            "metadata.section_type": "Submission_Respondent",
            "document_type": "judgment"
        }
        
        prosecution_results = await vector_search(
            query=facts,
            top_k=10,
            filters=prosecution_filters
        )
        
        logger.info(f"Retrieved {len(prosecution_results)} prosecution argument chunks")
        print("\n[FACT MINER] Prosecution Chunks from RAG:")
        for i, chunk in enumerate(prosecution_results, 1):
            print(f"  [Prosecution Chunk {i}]: {chunk}")
            content = chunk.get("supporting_quote") or chunk.get("raw_content")
            if content:
                prosecution_args.append(content)

        # Search for defense arguments (Submission_Petitioner)
        defense_filters = {
            "metadata.section_type": "Submission_Petitioner",
            "document_type": "judgment"
        }
        
        defense_results = await vector_search(
            query=facts,
            top_k=10,
            filters=defense_filters
        )
        
        logger.info(f"Retrieved {len(defense_results)} defense argument chunks")
        print("\n[FACT MINER] Defense Chunks from RAG:")
        for i, chunk in enumerate(defense_results, 1):
            print(f"  [Defense Chunk {i}]: {chunk}")
            content = chunk.get("supporting_quote") or chunk.get("raw_content")
            if content:
                defense_args.append(content)

        # Remove duplicates while preserving order
        def dedup(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]

        prosecution_args = dedup(prosecution_args)
        defense_args = dedup(defense_args)

        logger.info(f"Mined {len(prosecution_args)} prosecution args, {len(defense_args)} defense args from Atlas chunks (deduplicated)")
        logger.info(f"=== Completed fact_miner ===")

        return {"prosecution": prosecution_args, "defense": defense_args}

    except Exception as e:
        logger.error(f"Error mining arguments from facts: {e}", exc_info=True)
        return {"prosecution": [], "defense": []}