import logging

from pydantic import BaseModel

from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent

from repositories.streamers import StreamerConfigRepository
from .twitch.authorize import authorize


logger = logging.getLogger(__name__)


class RewardRedemption(BaseModel):
    broadcaster_user_id: str
    broadcaster_user_login: str
    user_name: str
    reward_title: str
    reward_prompt: str

    @classmethod
    def from_twitch_event(cls, event: ChannelPointsCustomRewardRedemptionAddEvent):
        return cls(
            broadcaster_user_id=event.event.broadcaster_user_id,
            broadcaster_user_login=event.event.broadcaster_user_login,
            user_name=event.event.user_name,
            reward_title=event.event.reward.title,
            reward_prompt=event.event.reward.prompt or "",
        )


async def on_redemption_reward_add(reward: RewardRedemption):
    logger.info(f"{reward.user_name} just redeemed {reward.reward_title}!")

    twitch = await authorize(reward.broadcaster_user_login)

    streamer = await StreamerConfigRepository.get_by_twitch_id(int(reward.broadcaster_user_id))

    if streamer.notifications.redemption_reward is None:
        return

    message = streamer.notifications.redemption_reward.format(
        user=reward.user_name,
        reward_title=reward.reward_title,
        reward_promt=f" ({reward.reward_prompt})" if reward.reward_prompt else ""
    )

    await twitch.send_chat_message(
        reward.broadcaster_user_id,
        reward.broadcaster_user_id,
        message
    )
