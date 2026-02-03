from guardrails import Validator, register_validator
from guardrails.validator_base import FailResult, PassResult, ValidationResult
from typing import Dict, Any, List, Callable
import re

@register_validator(name="grounded_in_context", data_type="string")
class GroundedInContext(Validator):
    def __init__(self, threshold: float = 0.7, on_fail: str = "noop", llm_callable: Callable = None, **kwargs):
        # kwargs to accept other params passed by Guardrails
        super().__init__(on_fail=on_fail, **kwargs)
        self.threshold = float(threshold)
        self.llm_callable = llm_callable

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        context = metadata.get("context", [])
        # Context might be a list of dicts (parsed from JSON) or raw list
        if not context:
             return FailResult(error_message="No context provided for grounding check.")
             
        # Normalize context to list of strings
        context_texts = []
        if isinstance(context, list):
            for c in context:
                if isinstance(c, dict):
                    context_texts.append(c.get("text", ""))
                elif isinstance(c, str):
                    context_texts.append(c)
        
        if not context_texts:
             return FailResult(error_message="Context chunks empty.")

        # If no LLM provided, fail (or fallback to basic check, but here we enforce LLM)
        if not self.llm_callable:
             return FailResult(error_message="LLM not configured for groundedness check.")

        # Construct Prompt
        context_str = "\n".join(context_texts)
        prompt = f"""
        You are a fact-checking assistant.
        Context:
        {context_str}

        Statement:
        {value}

        Is the statement supported by the context? Answer only 'YES' or 'NO'.
        """
        
        try:
            response = self.llm_callable(prompt)
            clean_response = response.strip().upper()
            
            if "YES" in clean_response:
                return PassResult()
            else:
                return FailResult(error_message="Statement not supported by context (LLM Verdict: NO)")
                
        except Exception as e:
            return FailResult(error_message=f"LLM Validation Failed: {str(e)}")
