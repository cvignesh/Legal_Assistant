"""
Judgment Ingestion Service - Async processing with MongoDB job persistence
"""
import uuid
import asyncio
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.judgment.parser import JudgmentParser
from app.services.judgment.models import JudgmentResult, JudgmentChunk
from app.services.embedder import embedder_service
from app.db.mongo import mongo
from app.core.config import settings
from app.services.ingestion import JobStatus


class JudgmentJob(BaseModel):
    """Judgment ingestion job"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_path: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[JudgmentResult] = None
    error: Optional[str] = None
    json_output_path: Optional[str] = None
    
    class Config:
        use_enum_values = True


# In-memory job store
judgment_job_store: Dict[str, JudgmentJob] = {}


class JudgmentIngestionService:
    def __init__(self):
        self.parser = JudgmentParser()
        # Ensure output directory exists
        self.output_dir = Path(settings.JUDGMENT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def create_job(self, file_path: str, filename: str) -> str:
        """Create a new judgment ingestion job and start parsing in background."""
        job = JudgmentJob(filename=filename, file_path=file_path)
        judgment_job_store[job.job_id] = job
        
        # Start background processing
        asyncio.create_task(self._process_parsing(job.job_id))
        
        return job.job_id

    async def _process_parsing(self, job_id: str):
        """Background task to run the judgment parser."""
        job = judgment_job_store.get(job_id)
        if not job:
            return

        try:
            job.status = JobStatus.PARSING
            
            # Run CPU-bound parser in thread pool
            result = await self.parser.process_pdf(job.file_path)
            
            if result.errors and not result.chunks:
                job.status = JobStatus.FAILED
                job.error = "; ".join(result.errors)
            else:
                job.result = result
                
                # Save JSON output
                json_path = self.output_dir / f"{job_id}.json"
                await self._save_json_output(result, json_path)
                job.json_output_path = str(json_path)
                
                # Auto-approve: proceed directly to indexing
                job.status = JobStatus.INDEXING
                asyncio.create_task(self._process_indexing(job))
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            import traceback
            traceback.print_exc()

    async def _save_json_output(self, result: JudgmentResult, output_path: Path):
        """Save parsed judgment result as JSON file."""
        try:
            # Convert to dict for JSON serialization
            output_data = {
                "filename": result.filename,
                "case_title": result.case_title,
                "court_name": result.court_name,
                "city": result.city,
                "year_of_judgment": result.year_of_judgment,
                "outcome": result.outcome,
                "winning_party": result.winning_party,
                "total_chunks": result.total_chunks,
                "chunks": [chunk.dict() for chunk in result.chunks],
                "errors": result.errors,
                "warnings": result.warnings
            }
            
            async with asyncio.Lock():
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                    
            print(f"   💾 Saved JSON output to {output_path}")
        except Exception as e:
            print(f"   ⚠️ Failed to save JSON: {e}")

    async def confirm_job(self, job_id: str):
        """Confirm a job, generate embeddings, and insert into DB."""
        job = judgment_job_store.get(job_id)
        if not job or job.status != JobStatus.PREVIEW_READY:
            raise ValueError("Job not ready for confirmation")
            
        job.status = JobStatus.INDEXING
        asyncio.create_task(self._process_indexing(job))
        return job.status

    async def _process_indexing(self, job: JudgmentJob):
        """Background task for embedding and indexing judgment chunks."""
        try:
            # Validate job has result
            if job.result is None:
                raise ValueError("Job result is None - parsing may have failed")
            
            if not job.result.chunks:
                raise ValueError("No chunks found in job result")
            
            chunks = job.result.chunks
            total_chunks = len(chunks)
            batch_size = settings.INGESTION_BATCH_SIZE
            
            print(f"Starting judgment indexing: {total_chunks} chunks, batch size: {batch_size}")
            
            # Ensure MongoDB is connected
            if mongo.db is None:
                print("MongoDB not connected, connecting now...")
                mongo.connect()
            
            # Prepare collection
            db = mongo.db
            if db is None:
                raise ValueError("Failed to connect to MongoDB - check MONGO_URI in .env")
                
            collection = db[settings.MONGO_COLLECTION_CHUNKS]
            
            # Batch process
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i : i + batch_size]
                texts = [c.text_for_embedding for c in batch]
                
                print(f"Embedding batch {i//batch_size + 1}: {len(texts)} chunks")
                
                # Generate Embeddings
                embeddings = await embedder_service.embed_batch(texts)
                
                print(f"Got {len(embeddings)} embeddings")
                
                # Prepare Documents for MongoDB
                docs = []
                for chunk, embedding in zip(batch, embeddings):
                    doc = chunk.dict()
                    doc["embedding"] = embedding
                    doc["created_at"] = datetime.utcnow()
                    doc["_id"] = chunk.chunk_id  # Use deterministic ID
                    doc["document_type"] = "judgment"  # Mark as judgment for filtering
                    docs.append(doc)
                
                # Upsert to MongoDB
                if docs:
                    # Using replace_one with upsert=True for idempotency
                    for doc in docs:
                        await collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                    print(f"Inserted batch {i//batch_size + 1} to MongoDB")
            
            job.status = JobStatus.COMPLETED
            print(f"Judgment indexing completed successfully")
            
        except Exception as e:
            print(f"Judgment indexing error: {str(e)}")
            import traceback
            traceback.print_exc()
            job.status = JobStatus.FAILED
            job.error = f"Indexing failed: {str(e)}"

    def get_job(self, job_id: str) -> Optional[JudgmentJob]:
        """Get a specific judgment job by ID."""
        return judgment_job_store.get(job_id)

    def get_all_jobs(self) -> List[JudgmentJob]:
        """Get all judgment jobs."""
        return list(judgment_job_store.values())


# Singleton instance
judgment_ingestion_service = JudgmentIngestionService()
