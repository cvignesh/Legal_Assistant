import pytest
import asyncio
from pathlib import Path
from app.db.mongo import mongo
from app.core.config import settings

# Test data for judgments
JUDGMENT_PDF_DIR = Path(__file__).parent.parent.parent.parent / "_legacy_poc" / "Judgment_parsing_POC"
TEST_JUDGMENTS = [
    ("Smt_Noor_Jahan_Begum_Anjali_Mishra_vs_State_Of_U_P_4_Others_on_16_December_2014.PDF", "Dismissed", "State"),
]

@pytest.mark.parametrize("pdf_filename,expected_outcome,expected_winner", TEST_JUDGMENTS)
@pytest.mark.asyncio
async def test_judgment_full_ingestion_with_mongodb(client, pdf_filename, expected_outcome, expected_winner):
    """
    End-to-end integration test for judgment processing:
    Upload -> Parse -> Preview -> Confirm -> Verify MongoDB.
    
    WARNING: This test will actually insert judgment data into your MongoDB database.
    Make sure you're using a test database or are okay with test data in production.
    """
    SAMPLE_PDF = JUDGMENT_PDF_DIR / pdf_filename
    
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample judgment PDF not found: {SAMPLE_PDF}")
    
    print(f"\n{'='*60}")
    print(f"Testing Judgment: {pdf_filename}")
    print(f"Expected Outcome: {expected_outcome}")
    print(f"Expected Winner: {expected_winner}")
    print(f"{'='*60}")
    
    # Step 1: Upload PDF
    with open(SAMPLE_PDF, "rb") as f:
        files = {"files": (pdf_filename, f, "application/pdf")}
        upload_response = await client.post("/api/judgments/upload", files=files)
    
    assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
    response_data = upload_response.json()
    assert response_data["total_uploaded"] == 1
    job_id = response_data["jobs"][0]["job_id"]
    print(f"\n✓ Uploaded judgment PDF, job_id: {job_id}")
    
    # Step 2: Wait for parsing to complete
    max_wait = 120  # Judgments take longer to parse (LLM calls)
    for i in range(max_wait):
        status_response = await client.get(f"/api/judgments/{job_id}/status")
        status = status_response.json()["status"]
        
        if status == "preview_ready":
            print(f"✓ Parsing completed in {i+1} seconds")
            break
        elif status == "failed":
            error = status_response.json().get("error")
            pytest.fail(f"Parsing failed: {error}")
        
        await asyncio.sleep(1)
    else:
        pytest.fail("Parsing timeout")
    
    # Step 3: Get preview and verify chunks
    preview_response = await client.get(f"/api/judgments/{job_id}/preview")
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    
    assert "chunks" in preview_data
    assert preview_data["total_chunks"] > 0
    chunk_count = preview_data["total_chunks"]
    
    # Verify global metadata
    assert preview_data["outcome"] == expected_outcome
    assert preview_data["winning_party"] == expected_winner
    assert preview_data["court_name"] is not None
    
    print(f"✓ Preview retrieved: {chunk_count} chunks")
    print(f"  - Case Title: {preview_data.get('case_title', 'N/A')}")
    print(f"  - Court: {preview_data.get('court_name', 'N/A')}")
    print(f"  - Year: {preview_data.get('year_of_judgment', 'N/A')}")
    
    # Verify chunk structure (anti-hallucination features)
    first_chunk = preview_data["chunks"][0]
    assert "supporting_quote" in first_chunk, "Missing supporting_quote field"
    assert "metadata" in first_chunk
    assert "section_type" in first_chunk["metadata"]
    assert "party_role" in first_chunk["metadata"]
    assert "legal_topics" in first_chunk["metadata"]
    
    print(f"✓ Verified anti-hallucination structure (supporting quotes present)")
    
    # Step 4: Confirm ingestion (this triggers embedding + MongoDB insertion)
    confirm_response = await client.post(f"/api/judgments/{job_id}/confirm")
    assert confirm_response.status_code == 200
    print(f"✓ Ingestion confirmed, indexing started")
    
    # Step 5: Wait for indexing to complete
    for i in range(90):  # 90 seconds max (embedding can take time)
        status_response = await client.get(f"/api/judgments/{job_id}/status")
        status = status_response.json()["status"]
        
        if status == "completed":
            print(f"✓ Indexing completed in {i+1} seconds")
            break
        elif status == "failed":
            error = status_response.json().get("error")
            pytest.fail(f"Indexing failed: {error}")
        
        await asyncio.sleep(1)
    else:
        pytest.fail("Indexing timeout")
    
    # Step 6: Verify data in MongoDB
    db = mongo.db
    collection = db[settings.MONGO_COLLECTION_CHUNKS]
    
    # Get first chunk from preview to verify
    first_chunk_id = preview_data["chunks"][0]["chunk_id"]
    
    # Query MongoDB
    doc = await collection.find_one({"_id": first_chunk_id})
    
    assert doc is not None, f"Chunk {first_chunk_id} not found in MongoDB"
    assert "embedding" in doc, "Embedding not found in MongoDB document"
    assert len(doc["embedding"]) == settings.EMBED_DIMENSION, f"Embedding dimension mismatch"
    assert doc["document_type"] == "judgment", "Document type should be 'judgment'"
    assert doc["metadata"]["outcome"] == expected_outcome
    assert doc["metadata"]["winning_party"] == expected_winner
    
    print(f"✓ Verified chunk in MongoDB: {first_chunk_id}")
    print(f"  - Embedding dimension: {len(doc['embedding'])}")
    print(f"  - Document type: {doc['document_type']}")
    print(f"  - Outcome: {doc['metadata']['outcome']}")
    
    # Step 7: Count total documents inserted
    total_docs = await collection.count_documents({
        "document_type": "judgment",
        "metadata.parent_doc": pdf_filename
    })
    print(f"✓ Total chunks in MongoDB for {pdf_filename}: {total_docs}")
    
    assert total_docs >= chunk_count, "Not all chunks were inserted"
    
    print("\n🎉 Full judgment ingestion pipeline test PASSED!")
    print(f"   - Parsed: {chunk_count} atomic units")
    print(f"   - Embedded: {chunk_count} vectors")
    print(f"   - Stored: {total_docs} documents in MongoDB")


@pytest.mark.asyncio
async def test_judgment_multiple_upload(client):
    """Test uploading multiple judgment PDFs at once."""
    SAMPLE_PDF = JUDGMENT_PDF_DIR / "Smt_Noor_Jahan_Begum_Anjali_Mishra_vs_State_Of_U_P_4_Others_on_16_December_2014.PDF"
    
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample judgment PDF not found: {SAMPLE_PDF}")
    
    print(f"\n{'='*60}")
    print(f"Testing Multiple Judgment Upload")
    print(f"{'='*60}")
    
    # Upload same PDF twice to test multiple upload
    files = [
        ("files", (SAMPLE_PDF.name, open(SAMPLE_PDF, "rb"), "application/pdf")),
        ("files", (SAMPLE_PDF.name, open(SAMPLE_PDF, "rb"), "application/pdf"))
    ]
    
    upload_response = await client.post("/api/judgments/upload", files=files)
    
    assert upload_response.status_code == 200
    response_data = upload_response.json()
    assert response_data["total_uploaded"] == 2
    assert len(response_data["jobs"]) == 2
    
    # Both should have unique job IDs
    job_ids = [job["job_id"] for job in response_data["jobs"]]
    assert len(job_ids) == len(set(job_ids)), "Job IDs should be unique"
    
    print(f"✓ Multiple upload successful: {len(job_ids)} jobs created")
    for job in response_data["jobs"]:
        print(f"  - Job ID: {job['job_id']}, Status: {job['status']}")


@pytest.mark.asyncio
async def test_judgment_list_jobs(client):
    """Test listing all judgment jobs."""
    # Upload a judgment first
    SAMPLE_PDF = JUDGMENT_PDF_DIR / "Smt_Noor_Jahan_Begum_Anjali_Mishra_vs_State_Of_U_P_4_Others_on_16_December_2014.PDF"
    
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample judgment PDF not found: {SAMPLE_PDF}")
    
    # Upload
    with open(SAMPLE_PDF, "rb") as f:
        files = {"files": (SAMPLE_PDF.name, f, "application/pdf")}
        await client.post("/api/judgments/upload", files=files)
    
    # List jobs
    list_response = await client.get("/api/judgments/jobs")
    assert list_response.status_code == 200
    jobs = list_response.json()
    
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    
    # Verify job structure
    for job in jobs:
        assert "job_id" in job
        assert "filename" in job
        assert "status" in job
        assert "created_at" in job
    
    print(f"✓ Listed {len(jobs)} judgment jobs")


@pytest.mark.asyncio
async def test_judgment_invalid_upload(client):
    """Test uploading non-PDF file to judgment endpoint."""
    # Create a fake non-PDF file
    files = {"files": ("test.txt", b"This is not a PDF", "text/plain")}
    
    upload_response = await client.post("/api/judgments/upload", files=files)
    
    assert upload_response.status_code == 200  # Doesn't fail, but rejects file
    response_data = upload_response.json()
    
    # Should have rejection in results
    rejected = [job for job in response_data["jobs"] if job["status"] == "rejected"]
    assert len(rejected) > 0
    assert "Only PDF files are supported" in rejected[0]["error"]
    
    print("✓ Invalid file correctly rejected")
