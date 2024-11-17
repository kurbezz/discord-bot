from datetime import datetime, timezone

from core.broker import broker
from repositories.streamers import StreamerConfigRepository

from .state import State
from .watcher import StateWatcher
from .twitch.authorize import authorize


@broker.task("stream_notifications.twitch.on_stream_state_change")
async def on_stream_state_change(
    streamer_id: int, new_state: State | None = None
):
    await StateWatcher.on_stream_state_change(streamer_id, new_state)


@broker.task(
    "stream_notifications.check_streams_states",
    schedule=[{"cron": "*/2 * * * *"}]
)
async def check_streams_states():
    streamers = await StreamerConfigRepository.all()
    streamers_ids = [str(streamer.twitch.id) for streamer in streamers]

    twitch = await authorize()

    async for stream in twitch.get_streams(user_id=streamers_ids):
        state = State(
            title=stream.title,
            category=stream.game_name,
            last_live_at=datetime.now(timezone.utc)
        )

        await StateWatcher.on_stream_state_change(int(stream.user_id), state)
