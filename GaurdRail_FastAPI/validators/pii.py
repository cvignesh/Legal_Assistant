from guardrails import Validator, register_validator
from guardrails.validator_base import FailResult, PassResult, ValidationResult
from typing import Dict, Any, Optional

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    print("Warning: Presidio not found, using regex fallback.")
    PRESIDIO_AVAILABLE = False

@register_validator(name="detect_pii", data_type="string")
class DetectPII(Validator):
    def __init__(self, mode: str = "redact", on_fail: str = "fix", **kwargs):
        super().__init__(on_fail=on_fail, **kwargs)
        self.mode = mode
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not PRESIDIO_AVAILABLE:
            # Fallback simple regex
            import re
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            phone_pattern = r'\d{3}-?\d{3}-?\d{4}'
            
            new_val = value
            found = False
            for pat in [email_pattern, phone_pattern]:
                if re.search(pat, new_val):
                    found = True
                    if self.mode == "redact":
                        new_val = re.sub(pat, "[REDACTED]", new_val)
            
            if found:
                return FailResult(error_message="PII detected (Basic Regex)", fix_value=new_val)
            return PassResult()

        # Presidio implementation
        # Note: 'en_core_web_lg' must be installed
        try:
            import os
            entities_str = os.getenv("PII_ENTITIES", "EMAIL_ADDRESS,PHONE_NUMBER,US_DRIVER_LICENSE,US_PASSPORT,US_SSN,PERSON,LOCATION")
            entities_list = [e.strip() for e in entities_str.split(",") if e.strip()]
            
            results = self.analyzer.analyze(text=value, entities=entities_list, language='en')
        except Exception as e:
            # Fallback if model load fails?
            print(f"Presidio error: {e}")
            return FailResult(error_message=f"PII Analysis Failed: {e}")

        if not results:
            return PassResult()
        
        if self.mode == "redact":
             result = self.anonymizer.anonymize(
                text=value,
                analyzer_results=results,
                operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})}
             )
             return FailResult(error_message="PII detected", fix_value=result.text)
        
        return FailResult(error_message="PII detected")
