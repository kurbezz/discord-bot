from datetime import timedelta

from temporalio import workflow
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

from applications.temporal_worker.queues import MAIN_QUEUE
from applications.twitch_webhook.activities.state_checker import check_streams_states


@workflow.defn
class StreamsCheckWorkflow:
    @classmethod
    def get_schedules(cls) -> dict[str, Schedule]:
        return {
            "check": Schedule(
                action=ScheduleActionStartWorkflow(
                    cls.run,
                    id="StreamsCheckWorkflow",
                    task_queue=MAIN_QUEUE,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))]
                )
            )
        }

    @workflow.run
    async def run(self):
        await workflow.start_activity(
            check_streams_states,
            task_queue=MAIN_QUEUE,
            schedule_to_close_timeout=timedelta(minutes=1)
        )
