import asyncio
from collections import Counter
from app.db.mongo import mongo
from app.core.config import settings

async def print_section_types(case_id: str):
    collection = mongo.db[settings.MONGO_COLLECTION_CHUNKS]
    query = {"metadata.case_number": case_id}
    cursor = collection.find(query)
    section_types = []
    async for doc in cursor:
        section_type = doc.get("metadata", {}).get("section_type")
        section_types.append(section_type)
    counter = Counter(section_types)
    print(f"Section type counts for case_number: {case_id}")
    for stype, count in counter.items():
        print(f"  {stype}: {count}")
    print(f"Unique section types: {list(counter.keys())}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python print_section_types.py <case_id>")
    else:
        mongo.connect()
        asyncio.run(print_section_types(sys.argv[1]))
        mongo.close()
