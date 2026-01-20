from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB]
        print(f"Connected to MongoDB: {settings.MONGO_DB}")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

    def get_collection(self, collection_name: str):
        """Get a specific collection."""
        return self.db[collection_name]

# Singleton instance
mongo = MongoDB()

async def get_database():
    """Dependency for API routes."""
    return mongo.db
