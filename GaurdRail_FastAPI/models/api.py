from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class ContextChunk(BaseModel):
    id: str
    text: str

class ValidatorConfig(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    mode: Optional[str] = None # For PII 'redact' or similar configs that might be top-level

class ValidationRequest(BaseModel):
    text: str
    context: Optional[List[ContextChunk]] = None
    validators: List[ValidatorConfig]

class ValidationError(BaseModel):
    validator: str
    message: str

class ValidationResponse(BaseModel):
    passed: bool
    errors: List[ValidationError] = Field(default_factory=list)
    validated_text: Optional[str] = None
