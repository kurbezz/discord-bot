from asyncio import run

from core.temporal import get_client

from temporalio.client import ScheduleAlreadyRunningError
from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from applications.schedule_sync import activities as schedule_sync_activities
from applications.schedule_sync.workflows import ScheduleSyncWorkflow

from .queues import MAIN_QUEUE


async def main():
    client = await get_client()

    for id, schedule in ScheduleSyncWorkflow.get_schedules().items():
        try:
            await client.create_schedule(f"ScheduleSyncWorkflow-{id}", schedule)
        except ScheduleAlreadyRunningError:
            pass

    worker: Worker = Worker(
        client,
        task_queue=MAIN_QUEUE,
        workflows=[
            ScheduleSyncWorkflow
        ],
        activities=[
            schedule_sync_activities.syncronize,
        ],
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    await worker.run()


run(main())
