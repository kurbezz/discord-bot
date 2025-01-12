from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from core.mongo import mongo_manager


class State(BaseModel):
    title: str
    category: str

    last_live_at: datetime

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, State):
            return False

        return self.title == value.title and self.category == value.category


class UpdateEvent(BaseModel):
    broadcaster_user_id: str
    title: str
    category_name: str


class EventType(StrEnum):
    STREAM_ONLINE = "stream.online"
    CHANNEL_UPDATE = "channel.update"
    UNKNOWN = "unknown"


class StateManager:
    COLLECTION_NAME = "stream_twitch_state"

    @classmethod
    async def get(cls, twitch_id: int) -> State | None:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            state = await collection.find_one({"twitch_id": twitch_id})
            if state is None:
                return None

            return State(**state)

    @classmethod
    async def update(cls, twitch_id: int, state: State):
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            await collection.update_one(
                {"twitch_id": twitch_id},
                {"$set": state.model_dump()},
                upsert=True
            )
