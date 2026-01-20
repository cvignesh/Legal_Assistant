from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_mistralai import MistralAIEmbeddings
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings # Uncomment if OpenAI is needed
from app.core.config import settings

@lru_cache()
def get_llm():
    """
    Factory to return the configured LLM provider.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return ChatGroq(
            api_key=settings.LLM_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
    # elif provider == "openai":
    #     return ChatOpenAI(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    
    raise ValueError(f"Unsupported LLM Provider: {provider}")

@lru_cache()
def get_embeddings():
    """
    Factory to return the configured Embedding provider.
    """
    provider = settings.EMBED_PROVIDER.lower()
    
    if provider == "mistral":
        return MistralAIEmbeddings(
            mistral_api_key=settings.EMBED_API_KEY,
            model=settings.EMBED_MODEL
        )
    # elif provider == "openai":
    #     return OpenAIEmbeddings(api_key=settings.EMBED_API_KEY, model=settings.EMBED_MODEL)

    raise ValueError(f"Unsupported Embedding Provider: {provider}")
