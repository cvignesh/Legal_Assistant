from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import importlib 
from dotenv import load_dotenv

load_dotenv()
os.environ["GUARDRAILS_NO_TELEMETRY"] = "true"

import warnings
# Suppress specific Guardrails warnings to keep logs clean
warnings.filterwarnings("ignore", message="We recommend including 'messages' as keyword-only arguments")
warnings.filterwarnings("ignore", message="Could not obtain an event loop")

from guardrails import Guard
# Dynamically loaded to handle missing hub installs
# from guardrails.hub import DetectPII 

from models.api import ValidationRequest, ValidationResponse, ValidationError, ValidatorConfig
from llm.factory import get_llm_callable
from validators import GroundedInContext, CitationsPresent, DetectPromptInjection, UnusualPrompt
from validators.pii import DetectPII

app = FastAPI(title="Guardrails Validation Service")

@app.on_event("startup")
async def startup_event():
    print("Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.methods}]")

# Registry of available validators
VALIDATORS_REGISTRY = {
    "grounded_in_context": GroundedInContext,
    "citations_present": CitationsPresent,
    "detect_pii": DetectPII,
    "detect_prompt_injection": DetectPromptInjection,
    "unusual_prompt": UnusualPrompt
}

@app.get("/")
async def root():
    return {"status": "running", "service": "Guardrails Validation Service", "docs": "/docs"}

@app.post("/validate", response_model=ValidationResponse)
async def validate_endpoint(request: ValidationRequest):
    # 1. Configure LLM
    llm_api = get_llm_callable()
    
    # 2. Instantiate Validators
    active_validators = []
    
    for v_config in request.validators:
        v_class = VALIDATORS_REGISTRY.get(v_config.name)
        if not v_class:
            raise HTTPException(status_code=400, detail=f"Unknown validator: {v_config.name}")
        
        # Prepare params
        params = v_config.parameters or {}
        
        # Inject LLM callable for strict validators
        if v_config.name in ["grounded_in_context", "detect_prompt_injection", "unusual_prompt"]:
            params["llm_callable"] = llm_api
        
        # Special handling for PII mode='redact' -> on_fail='fix'
        mode = getattr(v_config, 'mode', None)
        if v_config.name == "detect_pii":
            if mode == "redact" or params.get("mode") == "redact":
                if "on_fail" not in params:
                    params["on_fail"] = "fix"
        
        try:
             # Instantiate
             validator_instance = v_class(**params)
             active_validators.append(validator_instance)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize validator {v_config.name}: {str(e)}")

    if not active_validators:
        # If no validators passed, just return text as is?
        return ValidationResponse(passed=True, validated_text=request.text)

    # 3. Create Guard
    # We create a temporary guard for this request
    guard = Guard(name="dynamic_guard")
    for validator in active_validators:
        guard.use(validator)
    
    # 4. Prepare Metadata
    metadata = {}
    if request.context:
        metadata["context"] = [c.model_dump() for c in request.context]
    
    try:
        # 5. Validate
        result = guard.validate(
            request.text,
            metadata=metadata,
            llm_api=llm_api if llm_api else None, 
        )
        
        passed = result.validation_passed
        validated_text = result.validated_output
        
        errors = []
        if not passed:
            # Extract errors from result.validation_summaries (available in 0.7.x)
            if hasattr(result, "validation_summaries"):
                 for summary in result.validation_summaries:
                     # Each summary might be a ValidationSummary object
                     v_name = getattr(summary, "validator_name", "unknown")
                     msg = getattr(summary, "error_message", "Validation failed")
                     errors.append(ValidationError(validator=v_name, message=msg))
            # Fallback if validation_summaries is empty or different structure
            elif hasattr(result, "failed_validations"):
                 for failure in result.failed_validations:
                    v_name = getattr(failure, "validator_name", "unknown")
                    msg = getattr(failure, "error_message", "Validation failed")
                    errors.append(ValidationError(validator=v_name, message=msg))

        return ValidationResponse(
            passed=passed,
            errors=errors,
            validated_text=validated_text
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation execution failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
