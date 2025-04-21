from datetime import timedelta

from temporalio import workflow
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

with workflow.unsafe.imports_passed_through():
    from applications.common.repositories.streamers import StreamerConfigRepository
    from applications.schedule_sync.activities import ScheduleSyncActivity


TASK_QUEUE = "main"


@workflow.defn
class ScheduleSyncWorkflow:
    @classmethod
    def get_schedules(cls) -> dict[str, Schedule]:
        return {
            "all": Schedule(
                action=ScheduleActionStartWorkflow(
                    cls.run,
                    id="ScheduleSyncWorkflow",
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=5))]
                )
            )
        }

    @workflow.run
    async def run(self):
        streamers = await StreamerConfigRepository().all()

        for streamer in streamers:
            if streamer.integrations.discord is None:
                continue

            await workflow.execute_activity_method(
                ScheduleSyncActivity.syncronize,
                streamer.twitch.id
            )
