from temporalio import activity
from dataclasses import dataclass

from applications.twitch_webhook.state import State, EventType
from applications.twitch_webhook.watcher import StateWatcher


@dataclass
class OnStreamStateChangeActivity:
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
