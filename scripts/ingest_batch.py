#!/usr/bin/env python3
"""
CLI Script for Batch PDF Ingestion
Usage: python scripts/ingest_batch.py --folder ./Sample_pdf
"""
import sys
import asyncio
import argparse
from pathlib import Path
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.parser.manager import ParserManager
from app.services.embedder import embedder_service
from app.db.mongo import mongo
from app.core.config import settings
from datetime import datetime


async def ingest_pdf(pdf_path: Path, parser: ParserManager) -> dict:
    """Process a single PDF and insert into MongoDB."""
    print(f"\n[{pdf_path.name}] Starting ingestion...")
    
    try:
        # Step 1: Parse
        print(f"[{pdf_path.name}] Parsing...")
        result = await asyncio.to_thread(parser.process_pdf, str(pdf_path))
        
        if result.errors and not result.chunks:
            print(f"[{pdf_path.name}] ❌ Parsing failed: {'; '.join(result.errors)}")
            return {"status": "failed", "error": result.errors}
        
        print(f"[{pdf_path.name}] ✓ Parsed {result.total_chunks} chunks")
        
        # Step 2: Embed
        print(f"[{pdf_path.name}] Generating embeddings...")
        texts = [c.text_for_embedding for c in result.chunks]
        embeddings = await embedder_service.embed_batch(texts)
        
        # Step 3: Insert to MongoDB
        print(f"[{pdf_path.name}] Inserting to database...")
        collection = mongo.db[settings.MONGO_COLLECTION_CHUNKS]
        
        docs = []
        for chunk, embedding in zip(result.chunks, embeddings):
            doc = chunk.dict()
            doc["embedding"] = embedding
            doc["created_at"] = datetime.utcnow()
            doc["_id"] = chunk.chunk_id
            docs.append(doc)
        
        # Bulk upsert
        for doc in docs:
            await collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        
        print(f"[{pdf_path.name}] ✅ Successfully ingested {len(docs)} chunks")
        return {"status": "success", "chunks": len(docs)}
        
    except Exception as e:
        print(f"[{pdf_path.name}] ❌ Error: {str(e)}")
        return {"status": "failed", "error": str(e)}


async def main(folder: Path):
    """Process all PDFs in a folder."""
    # Connect to MongoDB
    mongo.connect()
    
    # Find all PDFs
    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {folder}")
        return
    
    print(f"\n🔍 Found {len(pdf_files)} PDF files")
    
    parser = ParserManager()
    results = []
    
    for pdf_path in pdf_files:
        result = await ingest_pdf(pdf_path, parser)
        results.append({"file": pdf_path.name, **result})
    
    # Summary
    print("\n" + "="*50)
    print("INGESTION SUMMARY")
    print("="*50)
    successes = sum(1 for r in results if r["status"] == "success")
    failures = sum(1 for r in results if r["status"] == "failed")
    total_chunks = sum(r.get("chunks", 0) for r in results)
    
    print(f"✅ Success: {successes}/{len(results)}")
    print(f"❌ Failed:  {failures}/{len(results)}")
    print(f"📦 Total Chunks Indexed: {total_chunks}")
    
    # Close MongoDB
    mongo.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch ingest PDF documents")
    parser.add_argument("--folder", type=str, required=True, help="Folder containing PDF files")
    
    args = parser.parse_args()
    folder_path = Path(args.folder)
    
    if not folder_path.exists():
        print(f"❌ Error: Folder '{folder_path}' does not exist")
        sys.exit(1)
    
    asyncio.run(main(folder_path))
