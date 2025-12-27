from motor.motor_asyncio import AsyncIOMotorClient
from farmora_backend.app.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_db(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.db = self.client[settings.DB_NAME]
        print("✅ Connected to MongoDB")

    async def close_db(self):
        if self.client:
            self.client.close()

db = Database()