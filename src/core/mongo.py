import contextlib

from mongojet import create_client

from core.config import config


async def create_mongo_client():
    return await create_client(config.MONGODB_URI)


class MongoDBSessionManager:
    def __init__(self):
        self.client = None

    async def init(self):
        self.client = await create_mongo_client()

    async def close(self):
        if self.client is not None:
            await self.client.close()

    @contextlib.asynccontextmanager
    async def connect(self):
        if self.client is None:
            await self.init()

        assert self.client is not None

        yield self.client


mongo_manager = MongoDBSessionManager()
