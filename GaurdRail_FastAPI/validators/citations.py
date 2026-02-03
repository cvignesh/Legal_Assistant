from guardrails import Validator, register_validator
from guardrails.validator_base import FailResult, PassResult, ValidationResult
import re
from typing import Dict, Any

@register_validator(name="citations_present", data_type="string")
class CitationsPresent(Validator):
    def __init__(self, on_fail: str = "noop"):
        super().__init__(on_fail=on_fail)

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        # Detect patterns like [1], [2], (Source: ...)
        # Detect patterns like [1], (Source: ...), Sources: ...
        pattern = r"\[\d+\]|\(?(?:Source|Sources|Ref): .*?\)?(?=[\s.]|$)"
        if re.search(pattern, value, re.IGNORECASE):
            return PassResult()
        
        return FailResult(
            error_message="Text is missing citations ([1] or (Source: ...)).",
            fix_value=value
        )
