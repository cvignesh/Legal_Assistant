import pytest
from pathlib import Path
from io import BytesIO

# Test data
SAMPLE_PDF = Path(__file__).parent.parent.parent.parent / "Sample_pdf" / "BNS.pdf"

@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db" in data

@pytest.mark.asyncio
async def test_upload_pdf(client):
    """Test PDF upload endpoint."""
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": ("BNS.pdf", f, "application/pdf")}
        response = await client.post("/api/ingest/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["filename"] == "BNS.pdf"
    assert data["status"] in ["queued", "parsing"]
    
    return data["job_id"]

@pytest.mark.asyncio
async def test_upload_invalid_file(client):
    """Test upload with non-PDF file."""
    files = {"file": ("test.txt", BytesIO(b"not a pdf"), "text/plain")}
    response = await client.post("/api/ingest/upload", files=files)
    
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_jobs(client):
    """Test listing all jobs."""
    response = await client.get("/api/ingest/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_job_status(client):
    """Test getting job status."""
    # First upload a file
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": ("BNS.pdf", f, "application/pdf")}
        upload_response = await client.post("/api/ingest/upload", files=files)
    
    job_id = upload_response.json()["job_id"]
    
    # Check status
    response = await client.get(f"/api/ingest/{job_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "filename" in data

@pytest.mark.asyncio
async def test_get_nonexistent_job(client):
    """Test getting status of non-existent job."""
    response = await client.get("/api/ingest/fake-job-id/status")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_full_ingestion_workflow(client):
    """Test complete workflow: Upload -> Wait -> Preview -> Confirm."""
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    # Step 1: Upload
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": ("BNS.pdf", f, "application/pdf")}
        upload_response = await client.post("/api/ingest/upload", files=files)
    
    job_id = upload_response.json()["job_id"]
    
    # Step 2: Wait for parsing (poll status)
    import asyncio
    max_wait = 30  # 30 seconds timeout
    for _ in range(max_wait):
        status_response = await client.get(f"/api/ingest/{job_id}/status")
        status = status_response.json()["status"]
        
        if status == "preview_ready":
            break
        elif status == "failed":
            pytest.fail(f"Parsing failed: {status_response.json().get('error')}")
        
        await asyncio.sleep(1)
    else:
        pytest.fail("Parsing timeout")
    
    # Step 3: Preview
    preview_response = await client.get(f"/api/ingest/{job_id}/preview")
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert "chunks" in preview_data
    assert preview_data["total_chunks"] > 0
    
    # Step 4: Confirm (Note: This will actually insert into DB)
    # Skip confirmation in tests to avoid DB pollution
    # confirm_response = await client.post(f"/api/ingest/{job_id}/confirm")
    # assert confirm_response.status_code == 200
