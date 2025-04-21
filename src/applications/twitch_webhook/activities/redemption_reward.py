from temporalio import activity

from applications.twitch_webhook.reward_redemption import RewardRedemption, on_redemption_reward_add


@activity.defn
async def on_redemption_reward_add_activity(event: RewardRedemption):
    await on_redemption_reward_add(event)
