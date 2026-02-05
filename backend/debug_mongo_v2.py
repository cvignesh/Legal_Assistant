
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def debug_mongo_v2():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["legal_documents"]
    
    print(f"Connected to DB: {settings.MONGO_DB}, Collection: legal_documents")

    # 1. Search for section_id "318" exactly
    print("\n--- 1. Exact match '318' ---")
    doc = await collection.find_one({"metadata.section_id": "318", "metadata.act_short": "BNS"})
    if doc:
        print("Found with exact match!")
    else:
        print("Not found with exact match.")

    # 2. Search for section_id "318" (Int)
    print("\n--- 2. Int match 318 ---")
    doc = await collection.find_one({"metadata.section_id": 318, "metadata.act_short": "BNS"})
    if doc:
        print("Found with int match!")
    else:
        print("Not found with int match.")

    # 3. Regex search for "318" in section_id
    print("\n--- 3. Regex match for '318' in section_id ---")
    cursor = collection.find({
        "metadata.act_short": "BNS", 
        "metadata.section_id": {"$regex": "318"}
    })
    found = False
    async for doc in cursor:
        found = True
        print(f"Found ID: {doc.get('_id')}")
        print(f"Section ID: {doc['metadata'].get('section_id')} (Type: {type(doc['metadata'].get('section_id'))})")
        print(f"Chunk Type: {doc['metadata'].get('chunk_type')}")
        print("-" * 20)
    if not found:
        print("No regex match found.")

    # 4. Search text content for "Section 318"
    print("\n--- 4. Content search for 'Section 318' ---")
    doc = await collection.find_one({
        "metadata.act_short": "BNS",
        "raw_content": {"$regex": "Section 318"}
    })
    if doc:
        print(f"Found in content! ID: {doc.get('_id')}")
        print(f"Metadata: {doc.get('metadata')}")
    else:
        print("Not found in content.")

    client.close()

if __name__ == "__main__":
    asyncio.run(debug_mongo_v2())
