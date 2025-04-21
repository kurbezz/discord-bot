from asyncio import run

from core.temporal import get_client

from temporalio.client import ScheduleAlreadyRunningError
from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from applications.schedule_sync import activities as schedule_sync_activities
from applications.schedule_sync.workflows import ScheduleSyncWorkflow

from applications.twitch_webhook import activities as twitch_activities
from applications.twitch_webhook import workflows as twitch_workflows

from .queues import MAIN_QUEUE


async def main():
    client = await get_client()

    for id, schedule in ScheduleSyncWorkflow.get_schedules().items():
        try:
            await client.create_schedule(f"ScheduleSyncWorkflow-{id}", schedule)
        except ScheduleAlreadyRunningError:
            pass

    for id, schedule in twitch_workflows.StreamsCheckWorkflow.get_schedules().items():
        try:
            await client.create_schedule(f"StreamsCheckWorkflow-{id}", schedule)
        except ScheduleAlreadyRunningError:
            pass

    worker: Worker = Worker(
        client,
        task_queue=MAIN_QUEUE,
        workflows=[
            ScheduleSyncWorkflow,
            twitch_workflows.StreamsCheckWorkflow,
            twitch_workflows.OnChannelUpdateWorkflow,
            twitch_workflows.OnMessageWorkflow,
            twitch_workflows.OnRewardRedemptionWorkflow,
            twitch_workflows.OnStreamOnlineWorkflow,
        ],
        activities=[
            schedule_sync_activities.syncronize,
            twitch_activities.on_message_activity,
            twitch_activities.on_stream_state_change_activity,
            twitch_activities.check_streams_states,
            twitch_activities.on_redemption_reward_add_activity,
        ],
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    await worker.run()


run(main())
