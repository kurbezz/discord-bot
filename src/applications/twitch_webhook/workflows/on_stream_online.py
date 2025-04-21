from temporalio import workflow

from applications.twitch_webhook.activities.on_state_change import on_stream_state_change_activity, OnStreamStateChangeActivity
from applications.twitch_webhook.state import EventType
from applications.temporal_worker.queues import MAIN_QUEUE


@workflow.defn
class OnStreamOnlineWorkflow:
    @workflow.run
    async def run(self, broadcaster_user_id: str, event_type: EventType):
        await workflow.start_activity(
            on_stream_state_change_activity,
            OnStreamStateChangeActivity(
                streamer_id=int(broadcaster_user_id),
                event_type=event_type
            ),
            task_queue=MAIN_QUEUE
        )
