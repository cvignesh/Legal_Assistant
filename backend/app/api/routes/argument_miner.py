from fastapi import APIRouter, HTTPException
from app.api.routes.schemas.amschemas import (
    ArgumentMinerRequest,
    ArgumentMinerResponse
)

from app.services.argument_miner.service import run_argument_miner

router = APIRouter(
    prefix="/argument-miner",
    tags=["Argument Miner"]
)


@router.post(
    "",
    response_model=ArgumentMinerResponse
)
async def argument_miner_endpoint(
    payload: ArgumentMinerRequest
):
    # ---- Validation ----
    if payload.mode in ("case", "hybrid") and not payload.case_id:
        raise HTTPException(
            status_code=400,
            detail="case_id is required for case or hybrid mode"
        )

    if payload.mode in ("facts", "hybrid") and not payload.facts:
        raise HTTPException(
            status_code=400,
            detail="facts are required for facts or hybrid mode"
        )

    # ---- Service call ----
    result = await run_argument_miner(
        case_id=payload.case_id,
        facts=payload.facts,
        mode=payload.mode
    )

    return result
