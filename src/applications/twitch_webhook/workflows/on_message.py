from temporalio import workflow

from applications.twitch_webhook.messages_proc import MessageEvent
from applications.twitch_webhook.activities.message_proc import on_message_activity
from applications.temporal_worker.queues import MAIN_QUEUE


@workflow.defn
class OnMessageWorkflow:
    @workflow.run
    async def run(self, message: MessageEvent) -> None:
        await workflow.start_activity(
            on_message_activity,
            message,
            task_queue=MAIN_QUEUE,
        )
