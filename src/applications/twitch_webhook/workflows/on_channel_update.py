from datetime import datetime, timezone, timedelta

from temporalio import workflow

from twitchAPI.helper import first

from applications.twitch_webhook.state import UpdateEvent, EventType, State
from applications.twitch_webhook.twitch.authorize import authorize
from applications.twitch_webhook.activities.on_state_change import on_stream_state_change_activity, OnStreamStateChangeActivity
from applications.temporal_worker.queues import MAIN_QUEUE


@workflow.defn
class OnChannelUpdateWorkflow:
    @workflow.run
    async def run(
        self,
        event: UpdateEvent,
        event_type: EventType,
    ):
        twitch = await authorize(event.broadcaster_user_login)

        stream = await first(twitch.get_streams(user_id=[event.broadcaster_user_id]))
        if stream is None:
            return

        await workflow.start_activity(
            on_stream_state_change_activity,
            OnStreamStateChangeActivity(
                int(event.broadcaster_user_id),
                event_type,
                State(
                    title=event.title,
                    category=event.category_name,
                    last_live_at=datetime.now(timezone.utc)
                ),
            ),
            task_queue=MAIN_QUEUE,
            schedule_to_close_timeout=timedelta(minutes=1)
        )
