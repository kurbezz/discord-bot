from datetime import datetime, timezone

from temporalio import activity

from pydantic import BaseModel

from twitchAPI.helper import first

from applications.twitch_webhook.state import State, EventType, UpdateEvent
from applications.twitch_webhook.watcher import StateWatcher
from applications.twitch_webhook.twitch.authorize import authorize


class OnStreamStateChangeActivity(BaseModel):
    streamer_id: int
    event_type: EventType
    new_state: State | None = None


@activity.defn
async def on_stream_state_change_activity(
    data: OnStreamStateChangeActivity
):
    await StateWatcher.on_stream_state_change(
        data.streamer_id,
        data.event_type,
        data.new_state,
    )


class OnChannelUpdateActivity(BaseModel):
    event: UpdateEvent
    event_type: EventType


@activity.defn
async def on_channel_update_activity(
    data: OnChannelUpdateActivity
):
    twitch = await authorize(data.event.broadcaster_user_login)

    stream = await first(twitch.get_streams(
        user_id=[data.event.broadcaster_user_id])
    )
    if stream is None:
        return

    await on_stream_state_change_activity(
        OnStreamStateChangeActivity(
            streamer_id=int(data.event.broadcaster_user_id),
            event_type=data.event_type,
            new_state=State(
                title=data.event.title,
                category=data.event.category_name,
                last_live_at=datetime.now(timezone.utc)
            ),
        )
    )
