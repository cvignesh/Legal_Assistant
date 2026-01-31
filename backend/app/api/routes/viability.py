from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.viability_service import viability_service, PredictionResult

router = APIRouter()

class ViabilityRequest(BaseModel):
    facts: str = Field(..., description="User's scenario description")
    user_role: str = Field(default="Petitioner", description="User's role (Petitioner/Respondent)")
    court_filter: Optional[str] = Field(default="All Courts", description="Filter by court name")

@router.post("", response_model=PredictionResult)
async def predict_viability(request: ViabilityRequest):
    """
    Predict case viability based on facts and historical precedents.
    """
    try:
        result = await viability_service.predict_viability(
            raw_facts=request.facts,
            user_role=request.user_role,
            court_filter=request.court_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
