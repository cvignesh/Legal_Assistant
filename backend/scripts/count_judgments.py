import sys
import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Load env from backend/.env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_CHUNKS")

async def count_judgments():
    if not MONGO_URI:
        print("❌ Error: MONGO_URI not found in .env")
        return

    print(f"Connecting to MongoDB...")
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[COLLECTION_NAME]

        # Filter for judgments only
        filter_query = {"document_type": "judgment"}
        
        # Count
        count = await collection.count_documents(filter_query)
        
        print(f"\n✅ Total Judgment Chunks in '{COLLECTION_NAME}': {count}")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(count_judgments())
