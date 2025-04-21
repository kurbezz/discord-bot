from temporalio import activity

from applications.twitch_webhook.state import State, EventType
from applications.twitch_webhook.watcher import StateWatcher


@activity.defn
async def on_stream_state_change_activity(
    streamer_id: int,
    event_type: EventType,
    new_state: State | None = None
):
    await StateWatcher.on_stream_state_change(
        streamer_id,
        event_type,
        new_state,
    )


# @activity.defn
# async def on_stream_state_change_with_check(
#     event: UpdateEvent,
#     event_type: EventType
# ):
#     twitch = await authorize(event.broadcaster_user_login)

#     stream = await first(twitch.get_streams(user_id=[event.broadcaster_user_id]))
#     if stream is None:
#         return

#     await on_stream_state_change.kiq(
#         int(event.broadcaster_user_id),
#         event_type,
#         State(
#             title=event.title,
#             category=event.category_name,
#             last_live_at=datetime.now(timezone.utc)
#         )
#     )
