import os
import openai
from typing import Optional, Callable, Any

def get_llm_callable() -> Optional[Callable[[str], str]]:
    """
    Returns a callable that takes a prompt and returns a string response,
    configured based on environment variables.
    """
    provider = os.getenv("VALIDATION_LLM_PROVIDER", "").lower()
    
    if not provider:
        return None
        
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("VALIDATION_LLM_MODEL", "gpt-3.5-turbo")
        if not api_key:
            # If provider is specified but key is missing, we interpret this as "configured but invalid",
            # but for a "factory" returning None means "no LLM available". 
            # The caller should handle "requested LLM validator but no LLM".
            return None 
            
        client = openai.OpenAI(api_key=api_key)
        
        def openai_callable(prompt: str, **kwargs) -> str:
            # Extract standard args if passed by Guardrails or custom logic
            model_to_use = kwargs.get("model", model)
            messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
            )
            return response.choices[0].message.content or ""
            
        return openai_callable

    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("VALIDATION_LLM_MODEL", "llama2")
        
        # Use openai client compatible with Ollama
        client = openai.OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        
        def ollama_callable(prompt: str, **kwargs) -> str:
            model_to_use = kwargs.get("model", model)
            messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        
        return ollama_callable
        
    elif provider == "groq":
        # Groq is OpenAI compatible
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("VALIDATION_LLM_MODEL", "llama3-70b-8192")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        
        if not api_key:
            return None
            
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        def groq_callable(prompt: str, **kwargs) -> str:
            model_to_use = kwargs.get("model", model)
            messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
            )
            return response.choices[0].message.content or ""
            
        return groq_callable

    return None
