from typing import List
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.factory import get_embeddings
from app.core.config import settings

class EmbedderService:
    def __init__(self):
        # We get the factory function, initialization happens on first access
        self._embedder = None

    @property
    def embedder(self):
        if not self._embedder:
            self._embedder = get_embeddings()
        return self._embedder

    @retry(
        stop=stop_after_attempt(settings.INGESTION_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts using the configured provider.
        Includes automatic retries for robustness.
        """
        if not texts:
            return []
            
        try:
            # LangChain's embed_documents is synchronous, run it in thread pool
            embeddings = await asyncio.to_thread(self.embedder.embed_documents, texts)
            
            # Validate result
            if embeddings is None:
                raise ValueError("Embedding service returned None - check API key and configuration")
            
            if not isinstance(embeddings, list):
                raise ValueError(f"Expected list of embeddings, got {type(embeddings)}")
            
            if len(embeddings) != len(texts):
                raise ValueError(f"Embedding count mismatch: got {len(embeddings)}, expected {len(texts)}")
            
            return embeddings
            
        except Exception as e:
            print(f"Embedding error: {str(e)}")
            raise

embedder_service = EmbedderService()
