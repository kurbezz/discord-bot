from datetime import timedelta

from temporalio import workflow

from applications.temporal_worker.queues import MAIN_QUEUE
from applications.twitch_webhook.activities.on_state_change import OnChannelUpdateActivity, on_channel_update_activity
from applications.twitch_webhook.state import UpdateEvent, EventType


@workflow.defn
class OnChannelUpdateWorkflow:
    @workflow.run
    async def run(
        self,
        event: UpdateEvent,
        event_type: EventType,
    ):
        await workflow.start_activity(
            on_channel_update_activity,
            OnChannelUpdateActivity(
                event=event,
                event_type=event_type,
            ),
            task_queue=MAIN_QUEUE,
            start_to_close_timeout=timedelta(minutes=1),
        )
