
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def debug_mongo():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["legal_documents"]
    
    print(f"Connected to DB: {settings.MONGO_DB}, Collection: legal_documents")

    # Try 1: Find by section_id "318" (String)
    print("\n--- Attempt 1: Search by metadata.section_id = '318' ---")
    doc = await collection.find_one({"metadata.section_id": "318"})
    if doc:
        print("FOUND!")
        print(f"Act Short: {doc.get('metadata', {}).get('act_short')}")
        print(f"Metadata: {doc.get('metadata')}")
    else:
        print("Not found.")

    # Try 2: Find by section_id 318 (Int)
    print("\n--- Attempt 2: Search by metadata.section_id = 318 (int) ---")
    doc = await collection.find_one({"metadata.section_id": 318})
    if doc:
        print("FOUND!")
        print(f"Act Short: {doc.get('metadata', {}).get('act_short')}")
        print(f"Metadata: {doc.get('metadata')}")
    else:
        print("Not found.")
        
    # Try 3: Broad search for 'BNS' to see Act name format
    print("\n--- Attempt 3: Search for any BNS document to check act_short ---")
    doc = await collection.find_one({"metadata.act_short": "BNS"})
    if doc:
        print("Found a BNS doc!")
        print(f"Metadata: {doc.get('metadata')}")
    else:
        print("No document with act_short='BNS' found.")
        # Try finding one with "Bharatiya" in text to guess the act_short
        print("Searching for 'Bharatiya' in metadata...")
        cursor = collection.find({"metadata.act": {"$regex": "Bharatiya"}}).limit(1)
        async for doc in cursor:
             print(f"Found alternative: {doc.get('metadata')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(debug_mongo())
