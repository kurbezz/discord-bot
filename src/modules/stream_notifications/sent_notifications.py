from enum import StrEnum
from datetime import datetime, timezone

from pydantic import BaseModel

from core.mongo import mongo_manager

from .state import State


class SentNotificationType(StrEnum):
    START_STREAM = "start_stream"
    CHANGE_CATEGORY = "change_category"


class SentNotification(BaseModel):
    notification_type: SentNotificationType
    twitch_id: int
    state: State
    sent_result: dict[str, bool]
    sent_at: datetime


class SentNotificationRepository:
    COLLECTION_NAME = "sent_notifications"

    @classmethod
    async def add(
        cls,
        twitch_id: int,
        notification_type: SentNotificationType,
        state: State,
        sent_result: dict[str, bool],
    ):
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            await collection.insert_one(
                SentNotification(
                    notification_type=notification_type,
                    twitch_id=twitch_id,
                    state=state,
                    sent_at=datetime.now(timezone.utc),
                    sent_result=sent_result,
                ).model_dump()
            )

    @classmethod
    async def get_last_for_streamer(
        cls, twitch_id: int
    ) -> SentNotification | None:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            doc = await collection.find_one(
                {"twitch_id": twitch_id},
                sort={"sent_at": -1},
            )
            if doc is None:
                return None

            return SentNotification(**doc)
