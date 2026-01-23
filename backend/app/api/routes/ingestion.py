import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from app.services.ingestion import ingestion_service, JobStatus
from app.services.parser.models import DocumentResult

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_document(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF files to start the ingestion process.
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
            job_id = await ingestion_service.create_job(tmp_path, file.filename)
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

@router.get("/jobs", response_model=list)
async def list_jobs():
    """List all ingestion jobs."""
    return ingestion_service.get_all_jobs()

@router.get("/{job_id}/status", response_model=dict)
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    job = ingestion_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "filename": job.filename,
        "error": job.error
    }

@router.get("/{job_id}/preview", response_model=DocumentResult)
async def get_job_preview(job_id: str):
    """Get the parsed chunks for review."""
    job = ingestion_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in [JobStatus.PREVIEW_READY, JobStatus.APPROVED, JobStatus.INDEXING, JobStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Preview not available yet (still parsing or failed)")
        
    return job.result

@router.post("/{job_id}/confirm", response_model=dict)
async def confirm_ingestion(job_id: str):
    """Confirm a job and start indexing."""
    try:
        status = await ingestion_service.confirm_job(job_id)
        return {"job_id": job_id, "status": status, "message": "Indexing started in background"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
