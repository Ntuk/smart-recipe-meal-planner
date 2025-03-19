from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self, url: str, max_pool_size: int = 100):
        self.url = url
        self.client: Optional[AsyncIOMotorClient] = None
        self.max_pool_size = max_pool_size
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Connect to MongoDB with connection pooling"""
        async with self._lock:
            try:
                if self.client is not None:
                    return True
                    
                self.client = AsyncIOMotorClient(
                    self.url,
                    maxPoolSize=self.max_pool_size,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                await self.client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                if self.client:
                    self.client.close()
                    self.client = None
                return False

    async def close(self):
        """Close MongoDB connection"""
        async with self._lock:
            if self.client:
                self.client.close()
                self.client = None
                logger.info("Closed MongoDB connection")

    async def get_database(self, db_name: str):
        """Get database instance"""
        async with self._lock:
            try:
                if not self.client:
                    if not await self.connect():
                        raise Exception("Failed to connect to MongoDB")
                
                db = self.client[db_name]
                # Verify database connection by executing a simple command
                await db.command("ping")
                return db
                
            except Exception as e:
                logger.error(f"Error getting database: {str(e)}")
                raise