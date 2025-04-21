from datetime import datetime, timezone

from twitchAPI.helper import first

from core.broker import broker
from applications.common.repositories.streamers import StreamerConfigRepository

from .state import State, UpdateEvent, EventType
from .watcher import StateWatcher
from .messages_proc import MessageEvent, MessagesProc
from .twitch.authorize import authorize
from .reward_redemption import RewardRedemption, on_redemption_reward_add


@broker.task(
    "stream_notifications.twitch.on_stream_state_change_with_check",
    retry_on_error=True
)
async def on_stream_state_change_with_check(
    event: UpdateEvent,
    event_type: EventType
):
    twitch = await authorize(event.broadcaster_user_login)

    stream = await first(twitch.get_streams(user_id=[event.broadcaster_user_id]))
    if stream is None:
        return

    await on_stream_state_change.kiq(
        int(event.broadcaster_user_id),
        event_type,
        State(
            title=event.title,
            category=event.category_name,
            last_live_at=datetime.now(timezone.utc)
        )
    )


@broker.task(
    "stream_notifications.twitch.on_stream_state_change",
    retry_on_error=True
)
async def on_stream_state_change(
    streamer_id: int,
    event_type: EventType,
    new_state: State | None = None
):
    await StateWatcher.on_stream_state_change(
        streamer_id,
        event_type,
        new_state,
    )


@broker.task(
    "stream_notifications.check_streams_states",
    schedule=[{"cron": "*/2 * * * *"}]
)
async def check_streams_states():
    streamers = await StreamerConfigRepository.all()
    streamers_ids = [str(streamer.twitch.id) for streamer in streamers]

    twitch = await authorize("kurbezz")

    async for stream in twitch.get_streams(user_id=streamers_ids):
        state = State(
            title=stream.title,
            category=stream.game_name,
            last_live_at=datetime.now(timezone.utc)
        )

        await StateWatcher.on_stream_state_change(
            int(stream.user_id),
            EventType.UNKNOWN,
            state
        )


@broker.task(
    "stream_notifications.on_message",
    retry_on_error=True
)
async def on_message(
    received_as: str,
    event: MessageEvent
):
    await MessagesProc.on_message(received_as, event)


@broker.task(
    "stream_notifications.on_redemption_reward_add",
    retry_on_error=True
)
async def on_redemption_reward_add_task(event: RewardRedemption):
    await on_redemption_reward_add(event)
