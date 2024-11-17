from domain.streamers import StreamerConfig

from core.mongo import mongo_manager


class StreamerConfigRepository:
    COLLECTION_NAME = "streamers"

    @classmethod
    async def get_by_twitch_id(cls, twitch_id: int) -> StreamerConfig:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            doc = await collection.find_one({"twitch.id": twitch_id})
            if doc is None:
                raise ValueError(f"Streamer with twitch id {twitch_id} not found")

            return StreamerConfig(**doc)

    @classmethod
    async def all(cls) -> list[StreamerConfig]:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            cursor = await collection.find()
            return [StreamerConfig(**doc) async for doc in cursor]
