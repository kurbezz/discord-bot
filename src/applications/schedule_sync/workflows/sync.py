from datetime import timedelta

from temporalio import workflow
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

from applications.common.repositories.streamers import StreamerConfigRepository
from applications.schedule_sync.activities import syncronize
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
            await workflow.start_activity(
                syncronize,
                streamer.twitch.id,
                schedule_to_close_timeout=timedelta(minutes=5),
            )
