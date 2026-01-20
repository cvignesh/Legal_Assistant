import pytest
import asyncio
from pathlib import Path
from app.db.mongo import mongo
from app.core.config import settings

# Test data
SAMPLE_PDF_DIR = Path(__file__).parent.parent.parent.parent / "Sample_pdf"
TEST_PDFS = [
    ("BNS.pdf", "Bharatiya Nyaya Sanhita"),
    ("BNSS.pdf", "Bharatiya Nagarik Suraksha Sanhita"),
]

@pytest.mark.parametrize("pdf_filename,expected_act_name", TEST_PDFS)
@pytest.mark.asyncio
async def test_full_ingestion_with_mongodb(client, pdf_filename, expected_act_name):
    """
    End-to-end integration test: Upload -> Parse -> Preview -> Confirm -> Verify MongoDB.
    
    WARNING: This test will actually insert data into your MongoDB database.
    Make sure you're using a test database or are okay with test data in production.
    """
    SAMPLE_PDF = SAMPLE_PDF_DIR / pdf_filename
    
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_filename}")
    print(f"Expected Act: {expected_act_name}")
    print(f"{'='*60}")
    
    # Step 1: Upload PDF
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": (pdf_filename, f, "application/pdf")}
        upload_response = await client.post("/api/ingest/upload", files=files)
    
    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]
    print(f"\n✓ Uploaded PDF, job_id: {job_id}")
    
    # Step 2: Wait for parsing to complete
    max_wait = 30
    for i in range(max_wait):
        status_response = await client.get(f"/api/ingest/{job_id}/status")
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
    preview_response = await client.get(f"/api/ingest/{job_id}/preview")
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    
    assert "chunks" in preview_data
    assert preview_data["total_chunks"] > 0
    chunk_count = preview_data["total_chunks"]
    print(f"✓ Preview retrieved: {chunk_count} chunks")
    
    # Step 4: Confirm ingestion (this triggers embedding + MongoDB insertion)
    confirm_response = await client.post(f"/api/ingest/{job_id}/confirm")
    assert confirm_response.status_code == 200
    print(f"✓ Ingestion confirmed, indexing started")
    
    # Step 5: Wait for indexing to complete
    for i in range(60):  # 60 seconds max (embedding can take time)
        status_response = await client.get(f"/api/ingest/{job_id}/status")
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
    assert doc["metadata"]["act_name"] == preview_data["act_name"]
    
    print(f"✓ Verified chunk in MongoDB: {first_chunk_id}")
    print(f"  - Embedding dimension: {len(doc['embedding'])}")
    print(f"  - Act name: {doc['metadata']['act_name']}")
    
    # Step 7: Count total documents inserted
    total_docs = await collection.count_documents({"metadata.act_name": preview_data["act_name"]})
    print(f"✓ Total chunks in MongoDB for {preview_data['act_name']}: {total_docs}")
    
    assert total_docs >= chunk_count, "Not all chunks were inserted"
    
    print("\n🎉 Full ingestion pipeline test PASSED!")
    print(f"   - Parsed: {chunk_count} chunks")
    print(f"   - Embedded: {chunk_count} vectors")
    print(f"   - Stored: {total_docs} documents in MongoDB")
