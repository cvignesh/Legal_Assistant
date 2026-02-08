from fastapi import APIRouter, HTTPException, Depends
from typing import Any

from app.services.drafting.service import drafting_service
from app.services.drafting.models import DraftingRequest, DraftingResponse

router = APIRouter()

@router.post("/generate", response_model=DraftingResponse)
async def generate_draft(request: DraftingRequest) -> Any:
    """
    Generate a legal petition draft based on user story.
    
    Flow:
    1. Extract Facts (LLM)
    2. Map Legal Sections (LLM)
    3. Verify Statutes & Fetch Grounded Judgments (Vector DB)
    4. Apply Rules & Templates (Deterministic)
    """
    try:
        return await drafting_service.generate_draft(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
