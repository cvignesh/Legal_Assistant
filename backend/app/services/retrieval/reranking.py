"""
Reranking services using Cohere and LLM
"""
from typing import List, Dict, Any
from app.core.config import settings
import logging
import httpx

logger = logging.getLogger(__name__)


async def cohere_rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int = None
) -> List[Dict[str, Any]]:
    """
    Rerank documents using Cohere's rerank API
    
    Args:
        query: User's search query
        documents: List of document chunks to rerank
        top_n: Number of top results to return
        
    Returns:
        Reranked list of documents with updated scores
    """
    if not settings.USE_COHERE_RERANK or not settings.COHERE_API_KEY:
        logger.warning("Cohere reranking disabled or API key not configured")
        return documents[:top_n] if top_n else documents
    
    if top_n is None:
        top_n = settings.COHERE_RERANK_TOP_N
    
    try:
        # Prepare documents for Cohere API
        texts = [doc.get("text_for_embedding", "") for doc in documents]
        
        # Call Cohere Rerank API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cohere.ai/v1/rerank",
                headers={
                    "Authorization": f"Bearer {settings.COHERE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.COHERE_RERANK_MODEL,
                    "query": query,
                    "documents": texts,
                    "top_n": top_n,
                    "return_documents": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        # Map reranked results back to original documents
        reranked_docs = []
        for item in result.get("results", []):
            index = item["index"]
            score = item["relevance_score"]
            
            # Update document with new rerank score
            doc = documents[index].copy()
            doc["rerank_score"] = score
            doc["original_score"] = doc.get("score", 0.0)
            doc["score"] = score  # Replace with rerank score
            reranked_docs.append(doc)
        
        logger.info(f"Cohere reranked {len(documents)} → {len(reranked_docs)} documents")
        return reranked_docs
        
    except Exception as e:
        logger.error(f"Cohere reranking error: {str(e)}")
        # Fallback: return original documents
        return documents[:top_n] if top_n else documents


async def llm_rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int = None
) -> List[Dict[str, Any]]:
    """
    Rerank documents using LLM-based scoring for legal relevance
    
    Args:
        query: User's search query
        documents: List of document chunks to rerank
        top_n: Number of top results to return
        
    Returns:
        Reranked list of documents with updated scores
    """
    if not settings.USE_LLM_RERANK:
        logger.warning("LLM reranking disabled")
        return documents[:top_n] if top_n else documents
    
    if top_n is None:
        top_n = settings.LLM_RERANK_TOP_N
    
    try:
        # Use dedicated rerank LLM config, fallback to main LLM if not set
        api_key = settings.LLM_RERANK_API_KEY or settings.GROQ_API_KEY
        model = settings.LLM_RERANK_MODEL
        temperature = settings.LLM_RERANK_TEMPERATURE
        
        # Import LLM service based on provider
        if settings.LLM_RERANK_PROVIDER == "groq":
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)
        else:
            # Can add other providers (OpenAI, etc.) here
            logger.warning(f"Unknown LLM provider: {settings.LLM_RERANK_PROVIDER}, using Groq")
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)
        
        # Build prompt for LLM reranking
        # Create numbered list of documents
        doc_list = ""
        for i, doc in enumerate(documents, 1):
            text = doc.get("text_for_embedding", "")[:500]  # Limit text length
            doc_list += f"{i}. {text}\n\n"
        
        prompt = f"""You are a legal research assistant. Rank the following legal text chunks by their relevance to the query.

Query: "{query}"

Documents:
{doc_list}

Instructions:
1. Rank documents by legal relevance and importance
2. Consider: precedent value, specificity, recency, authority
3. Return ONLY a JSON array of document numbers in ranked order (most relevant first)
4. Example: [3, 1, 5, 2, 4]

Ranked order:"""
        
        # Call LLM
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a legal research expert. Respond with only a JSON array."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=200
        )
        
        # Parse LLM response
        import json
        ranking_text = response.choices[0].message.content.strip()
        
        # Extract JSON array from response
        import re
        json_match = re.search(r'\[[\d,\s]+\]', ranking_text)
        if not json_match:
            logger.warning("LLM reranking failed to parse response, using original order")
            return documents[:top_n]
        
        ranking = json.loads(json_match.group())
        
        # Reorder documents based on LLM ranking
        reranked_docs = []
        for rank_idx, doc_num in enumerate(ranking[:top_n]):
            if 1 <= doc_num <= len(documents):
                doc = documents[doc_num - 1].copy()
                # Assign score based on rank (1.0 for first, decreasing)
                doc["llm_rank_score"] = 1.0 - (rank_idx / len(ranking))
                doc["llm_rank"] = rank_idx + 1
                reranked_docs.append(doc)
        
        logger.info(f"LLM reranked {len(documents)} → {len(reranked_docs)} documents")
        return reranked_docs
        
    except Exception as e:
        logger.error(f"LLM reranking error: {str(e)}")
        # Fallback: return original documents
        return documents[:top_n] if top_n else documents
