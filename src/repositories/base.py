import abc

from contextlib import asynccontextmanager

from core.mongo import mongo_manager


class BaseRepository(abc.ABC):
    COLLECTION_NAME: str

    @asynccontextmanager
    @classmethod
    async def connect(cls):
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            yield collection
