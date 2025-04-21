from datetime import datetime, timezone

from temporalio import activity

from applications.common.repositories.streamers import StreamerConfigRepository
from applications.twitch_webhook.twitch.authorize import authorize
from applications.twitch_webhook.state import State, EventType
from applications.twitch_webhook.watcher import StateWatcher


@activity.defn
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
