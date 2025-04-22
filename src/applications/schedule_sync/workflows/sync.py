from datetime import timedelta

from temporalio import workflow
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

from applications.schedule_sync.activities import syncronize_all
from applications.temporal_worker.queues import MAIN_QUEUE


@workflow.defn
class ScheduleSyncWorkflow:
    @classmethod
    def get_schedules(cls) -> dict[str, Schedule]:
        return {
            "all": Schedule(
                action=ScheduleActionStartWorkflow(
                    cls.run,
                    id="ScheduleSyncWorkflow",
                    task_queue=MAIN_QUEUE,
                    execution_timeout=timedelta(minutes=1),
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=5))]
                )
            )
        }

    @workflow.run
    async def run(self):
        await workflow.execute_activity(
            syncronize_all,
            task_queue=MAIN_QUEUE,
            schedule_to_close_timeout=timedelta(minutes=5),
        )
