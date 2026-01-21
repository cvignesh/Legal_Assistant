"""
Judgment Processing API Routes
"""
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from app.services.judgment.ingestion import judgment_ingestion_service, JudgmentJob
from app.services.judgment.models import JudgmentResult
from app.services.ingestion import JobStatus

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_judgments(files: List[UploadFile] = File(...)):
    """
    Upload one or more judgment PDF files to start the ingestion process.
    Returns a list of job_ids for tracking.
    """
    job_results = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            job_results.append({
                "filename": file.filename,
                "status": "rejected",
                "error": "Only PDF files are supported"
            })
            continue
        
        # Save to temp file
        try:
            suffix = Path(file.filename).suffix
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
        except Exception as e:
            job_results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Failed to save upload: {str(e)}"
            })
            continue
        
        # Create ingestion job
        try:
            job_id = await judgment_ingestion_service.create_job(tmp_path, file.filename)
            job_results.append({
                "job_id": job_id,
                "filename": file.filename,
                "status": JobStatus.QUEUED
            })
        except Exception as e:
            job_results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Failed to create job: {str(e)}"
            })
    
    return {
        "total_uploaded": len(files),
        "jobs": job_results
    }


@router.get("/jobs", response_model=List[dict])
async def list_judgment_jobs():
    """List all judgment ingestion jobs."""
    jobs = judgment_ingestion_service.get_all_jobs()
    return [
        {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "error": job.error
        }
        for job in jobs
    ]


@router.get("/{job_id}/status", response_model=dict)
async def get_judgment_job_status(job_id: str):
    """Get the status of a specific judgment job."""
    job = judgment_ingestion_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job.job_id,
        "status": job.status,
        "filename": job.filename,
        "created_at": job.created_at.isoformat(),
        "error": job.error
    }
    
    # Add summary info if parsing is complete
    if job.result:
        response["summary"] = {
            "case_title": job.result.case_title,
            "court_name": job.result.court_name,
            "city": job.result.city,
            "year_of_judgment": job.result.year_of_judgment,
            "outcome": job.result.outcome,
            "winning_party": job.result.winning_party,
            "total_chunks": job.result.total_chunks,
            "errors": len(job.result.errors),
            "warnings": len(job.result.warnings)
        }
    
    return response


@router.get("/{job_id}/preview", response_model=JudgmentResult)
async def get_judgment_preview(job_id: str):
    """Get the parsed judgment chunks for review."""
    job = judgment_ingestion_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in [JobStatus.PREVIEW_READY, JobStatus.APPROVED, JobStatus.INDEXING, JobStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail=f"Preview not available yet (current status: {job.status})"
        )
        
    return job.result


@router.post("/{job_id}/confirm", response_model=dict)
async def confirm_judgment_ingestion(job_id: str):
    """Confirm a judgment job and start indexing to vector database."""
    try:
        status = await judgment_ingestion_service.confirm_job(job_id)
        return {
            "job_id": job_id,
            "status": status,
            "message": "Judgment indexing started in background"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
