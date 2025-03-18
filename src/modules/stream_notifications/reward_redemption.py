import logging

from pydantic import BaseModel

from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent

from core.config import config
from .twitch.authorize import authorize


logger = logging.getLogger(__name__)


class RewardRedemption(BaseModel):
    broadcaster_user_id: str
    user_name: str
    reward_title: str
    reward_prompt: str

    @classmethod
    def from_twitch_event(cls, event: ChannelPointsCustomRewardRedemptionAddEvent):
        return cls(
            broadcaster_user_id=event.event.broadcaster_user_id,
            user_name=event.event.user_name,
            reward_title=event.event.reward.title,
            reward_prompt=event.event.reward.prompt or "",
        )


async def on_redemption_reward_add(reward: RewardRedemption):
    logger.info(f"{reward.user_name} just redeemed {reward.reward_title}!")

    twitch = await authorize()

    await twitch.send_chat_message(
        reward.broadcaster_user_id,
        config.TWITCH_ADMIN_USER_ID,
        f"🎉 {reward.user_name} just redeemed {reward.reward_title}! 🎉"
    )
