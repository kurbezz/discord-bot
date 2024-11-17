from core.broker import broker

from .watcher import StateWatcher


@broker.task("stream_notifications.twitch.on_stream_state_change")
async def on_stream_state_change(streamer_id: int):
    await StateWatcher.on_stream_state_change(streamer_id)
