import asyncio
from app.db.mongo import mongo
from app.core.config import settings

async def inspect_case_chunks(case_id: str):
    collection = mongo.db[settings.MONGO_COLLECTION_CHUNKS]
    query = {"metadata.case_number": case_id}
    print(f"Querying for case_number: {case_id}")
    cursor = collection.find(query)
    count = 0
    async for doc in cursor:
        print(f"Chunk ID: {doc.get('chunk_id')}")
        print(f"  Section Type: {doc.get('metadata', {}).get('section_type')}")
        print(f"  Raw Content: {doc.get('raw_content', '')[:200]}")
        print(f"  Metadata: {doc.get('metadata')}")
        print("---")
        count += 1
    print(f"Total chunks found: {count}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python inspect_case_chunks.py <case_id>")
    else:
        mongo.connect()
        asyncio.run(inspect_case_chunks(sys.argv[1]))
        mongo.close()
