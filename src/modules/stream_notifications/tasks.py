from core.broker import broker

from .state import State
from .watcher import StateWatcher


@broker.task("stream_notifications.twitch.on_stream_state_change")
async def on_stream_state_change(
    streamer_id: int, new_state: State | None = None
):
    await StateWatcher.on_stream_state_change(streamer_id, new_state)
