from asyncio import run

from temporalio.client import Client, ScheduleAlreadyRunningError
from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from applications.schedule_sync.activities import ScheduleSyncActivity
from applications.schedule_sync.workflows import ScheduleSyncWorkflow


TASK_QUEUE = "main"


async def main():
    client: Client = await Client.connect("temporal:7233", namespace="default")

    for id, schedule in ScheduleSyncWorkflow.get_schedules().items():
        try:
            await client.create_schedule(f"ScheduleSyncWorkflow-{id}", schedule)
        except ScheduleAlreadyRunningError:
            pass

    worker: Worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            ScheduleSyncWorkflow
        ],
        activities=[
            ScheduleSyncActivity.syncronize
        ],
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    await worker.run()


run(main())
