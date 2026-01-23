import uuid
import asyncio
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.parser.manager import ParserManager
from app.services.parser.models import DocumentResult, LegalChunk
from app.services.embedder import embedder_service
from app.db.mongo import mongo, get_database
from app.core.config import settings

class JobStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    PREVIEW_READY = "preview_ready"
    APPROVED = "approved"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"

class IngestionJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_path: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[DocumentResult] = None
    error: Optional[str] = None
    
    class Config:
        use_enum_values = True

# In-memory job store (Replace with Redis/DB for production)
job_store: Dict[str, IngestionJob] = {}

class IngestionService:
    def __init__(self):
        self.parser = ParserManager()

    async def create_job(self, file_path: str, filename: str) -> str:
        """Create a new ingestion job and start parsing in background."""
        job = IngestionJob(filename=filename, file_path=file_path)
        job_store[job.job_id] = job
        
        # Start background processing
        asyncio.create_task(self._process_parsing(job.job_id))
        
        return job.job_id

    async def _process_parsing(self, job_id: str):
        """Background task to run the parser."""
        job = job_store.get(job_id)
        if not job:
            return

        try:
            job.status = JobStatus.PARSING
            # Run CPU-bound parser in thread pool
            result = await asyncio.to_thread(self.parser.process_pdf, job.file_path)
            
            if result.errors and not result.chunks:
                job.status = JobStatus.FAILED
                job.error = "; ".join(result.errors)
            else:
                job.result = result
                # Auto-approve: proceed directly to indexing
                job.status = JobStatus.INDEXING
                asyncio.create_task(self._process_indexing(job))
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)

    async def confirm_job(self, job_id: str):
        """Confirm a job, generate embeddings, and insert into DB."""
        job = job_store.get(job_id)
        if not job or job.status != JobStatus.PREVIEW_READY:
            raise ValueError("Job not ready for confirmation")
            
        job.status = JobStatus.INDEXING
        asyncio.create_task(self._process_indexing(job))
        return job.status

    async def _process_indexing(self, job: IngestionJob):
        """Background task for embedding and indexing."""
        try:
            # Validate job has result
            if job.result is None:
                raise ValueError("Job result is None - parsing may have failed")
            
            if not job.result.chunks:
                raise ValueError("No chunks found in job result")
            
            chunks = job.result.chunks
            total_chunks = len(chunks)
            batch_size = settings.INGESTION_BATCH_SIZE
            
            print(f"Starting indexing: {total_chunks} chunks, batch size: {batch_size}")
            
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
                    doc["_id"] = chunk.chunk_id # Use deterministic ID
                    docs.append(doc)
                
                # Upsert to MongoDB
                if docs:
                    # Using replace_one with upsert=True for idempotency
                    for doc in docs:
                         await collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                    print(f"Inserted batch {i//batch_size + 1} to MongoDB")
            
            job.status = JobStatus.COMPLETED
            print(f"Indexing completed successfully")
            
        except Exception as e:
            print(f"Indexing error: {str(e)}")
            import traceback
            traceback.print_exc()
            job.status = JobStatus.FAILED
            job.error = f"Indexing failed: {str(e)}"

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        return job_store.get(job_id)

    def get_all_jobs(self) -> List[IngestionJob]:
        return list(job_store.values())

ingestion_service = IngestionService()
