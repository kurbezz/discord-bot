from datetime import datetime, timezone, timedelta

from twitchAPI.helper import first

from core.redis import redis_manager
from repositories.streamers import StreamerConfigRepository

from .state import State, StateManager
from .sent_notifications import SentNotificationRepository, SentNotificationType
from .notification import notify
from .twitch.authorize import authorize


class StateWatcher:
    START_STREAM_THRESHOLD = timedelta(minutes=15)

    @classmethod
    async def get_twitch_state(cls, streamer_id: int) -> State | None:
        twitch = await authorize()

        stream = await first(
            twitch.get_streams(user_id=[str(streamer_id)])
        )

        if stream is None:
            return None

        return State(
            title=stream.title,
            category=stream.game_name,
            last_live_at=datetime.now(timezone.utc)
        )

    @classmethod
    async def notify_and_save(
        cls,
        streamer_id: int,
        sent_notification_type: SentNotificationType,
        state: State
    ):
        streamer = await StreamerConfigRepository.get_by_twitch_id(streamer_id)

        sent_result = await notify(sent_notification_type, streamer, state)
        await SentNotificationRepository.add(
            streamer.twitch.id,
            sent_notification_type,
            state,
            sent_result=sent_result
        )

    @classmethod
    async def notify_start_stream(
        cls,
        streamer_id: int,
        state: State
    ):
        await cls.notify_and_save(streamer_id, SentNotificationType.START_STREAM, state)

    @classmethod
    async def notify_change_category(
        cls,
        streamer_id: int,
        state: State
    ):
        await cls.notify_and_save(streamer_id, SentNotificationType.CHANGE_CATEGORY, state)

    @classmethod
    async def _on_stream_state_change(cls, streamer_id: int, new_state: State | None = None):
        if new_state is not None:
            current_state = new_state
        else:
            current_state = await cls.get_twitch_state(streamer_id)

        if current_state is None:
            return

        last_state = await StateManager.get(streamer_id)
        if last_state is None:
            await cls.notify_start_stream(streamer_id, current_state)
            await StateManager.update(streamer_id, current_state)
            return

        if datetime.now(timezone.utc) - last_state.last_live_at > cls.START_STREAM_THRESHOLD:
            await cls.notify_start_stream(streamer_id, current_state)
            await StateManager.update(streamer_id, current_state)
            return

        if last_state.category != current_state.category:
            await cls.notify_change_category(streamer_id, current_state)
            await StateManager.update(streamer_id, current_state)
            return

        await StateManager.update(streamer_id, current_state)

    @classmethod
    async def on_stream_state_change(cls, streamer_id: int, new_state: State | None = None):
        async with redis_manager.connect() as redis:
            async with redis.lock(f"on_stream_state_change:{streamer_id}"):
                await cls._on_stream_state_change(streamer_id, new_state)
