import asyncio
from app.db.mongo import mongo
from app.core.config import settings

async def print_argument_chunk_contents(case_id: str, section_type: str, limit: int = 10):
    collection = mongo.db[settings.MONGO_COLLECTION_CHUNKS]
    query = {"metadata.case_number": case_id, "metadata.section_type": section_type}
    cursor = collection.find(query).limit(limit)
    count = 0
    print(f"Showing up to {limit} chunks for case_number: {case_id}, section_type: {section_type}\n")
    async for doc in cursor:
        print(f"Chunk ID: {doc.get('chunk_id')}")
        print(f"  Raw Content: {doc.get('raw_content', '')[:300]}")
        print(f"  Supporting Quote: {doc.get('supporting_quote', '')[:300]}")
        print(f"  Metadata: {doc.get('metadata')}")
        print("---")
        count += 1
    print(f"Total shown: {count}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python print_argument_chunk_contents.py <case_id> <section_type>")
    else:
        mongo.connect()
        asyncio.run(print_argument_chunk_contents(sys.argv[1], sys.argv[2]))
        mongo.close()
