from temporalio import workflow

from applications.twitch_webhook.activities.redemption_reward import on_redemption_reward_add_activity
from applications.twitch_webhook.reward_redemption import RewardRedemption
from applications.temporal_worker.queues import MAIN_QUEUE


@workflow.defn
class OnRewardRedemptionWorkflow:
    @workflow.run
    async def run(self, reward: RewardRedemption):
        await workflow.start_activity(
            on_redemption_reward_add_activity,
            reward,
            task_queue=MAIN_QUEUE
        )
