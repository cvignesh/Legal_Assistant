from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # Database
    MONGO_URI: str
    MONGO_DB: str = "legal_db"
    MONGO_COLLECTION_CHUNKS: str = "legal_chunks_v1"
    MONGO_COLLECTION_JUDGMENT_JOBS: str = "judgment_jobs"  # Persistent job storage

    # LLM (Groq)
    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4096

    # Embeddings (Mistral/OpenAI)
    EMBED_PROVIDER: str = "mistral"
    EMBED_API_KEY: str
    EMBED_MODEL: str = "mistral-embed"
    EMBED_DIMENSION: int = 1024

    # Ingestion
    DOC_MAX_FILE_SIZE_MB: int = 25
    INGESTION_MAX_RETRIES: int = 3
    INGESTION_BATCH_SIZE: int = 10

    # Judgment Processing (Groq)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TEMPERATURE: float = 0.0
    FUZZY_MATCH_THRESHOLD: float = 0.60
    JUDGMENT_OUTPUT_DIR: str = "data/judgments"

    # ============================================
    # HYBRID SEARCH RETRIEVAL PIPELINE
    # ============================================
    
    # MongoDB Atlas Search Index Names
    VECTOR_INDEX_NAME: str = "vector_index"
    TEXT_INDEX_NAME: str = "text_index"
    
    # Vector Search Configuration
    VECTOR_SEARCH_TOP_K: int = 100
    VECTOR_MIN_SCORE: float = 0.6
    
    # Keyword Search Configuration  
    KEYWORD_SEARCH_TOP_K: int = 100
    KEYWORD_MIN_SCORE: float = 0.3
    
    # Deduplication Strategy
    DEDUP_METHOD: str = "id"  # Options: "id", "similarity", "both"
    DEDUP_SIMILARITY_THRESHOLD: float = 0.95
    
    # Reranking Configuration
    USE_COHERE_RERANK: bool = True
    COHERE_API_KEY: Optional[str] = None
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"
    COHERE_RERANK_TOP_N: int = 20
    
    USE_LLM_RERANK: bool = True
    LLM_RERANK_PROVIDER: str = "groq"  # Options: groq, openai, etc.
    LLM_RERANK_API_KEY: Optional[str] = None  # Defaults to GROQ_API_KEY if None
    LLM_RERANK_MODEL: str = "llama-3.3-70b-versatile"
    LLM_RERANK_TEMPERATURE: float = 0.0
    LLM_RERANK_TOP_N: int = 10
    
    # Score Fusion Weights (must sum to 1.0)
    VECTOR_SCORE_WEIGHT: float = 0.7
    KEYWORD_SCORE_WEIGHT: float = 0.3

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
