from asyncio import sleep, gather, wait, FIRST_COMPLETED, create_task
import logging
from typing import Literal

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.twitch import Twitch
from twitchAPI.object.eventsub import StreamOnlineEvent, ChannelUpdateEvent, ChannelChatMessageEvent, ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.oauth import validate_token

from core.temporal import get_client

from applications.common.repositories.streamers import StreamerConfigRepository, StreamerConfig
from applications.twitch_webhook.state import UpdateEvent, EventType
from applications.twitch_webhook.messages_proc import MessageEvent
from applications.twitch_webhook.reward_redemption import RewardRedemption
from applications.twitch_webhook.workflows.on_message import OnMessageWorkflow
from applications.twitch_webhook.workflows.on_reward_redemption import OnRewardRedemptionWorkflow
from applications.twitch_webhook.workflows.on_stream_online import OnStreamOnlineWorkflow
from applications.twitch_webhook.workflows.on_channel_update import OnChannelUpdateWorkflow
from applications.temporal_worker.queues import MAIN_QUEUE
from .authorize import authorize


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TwitchService:
    ONLINE_NOTIFICATION_DELAY = 15 * 60

    def __init__(self, twitch: Twitch, streamer: StreamerConfig):
        self.twitch = twitch
        self.streamer = streamer

        self.failed = False

    async def on_channel_update(self, event: ChannelUpdateEvent):
        client = await get_client()

        await client.start_workflow(
            OnChannelUpdateWorkflow.run,
            args=(
                UpdateEvent(
                    broadcaster_user_id=event.event.broadcaster_user_id,
                    broadcaster_user_login=event.event.broadcaster_user_login,
                    title=event.event.title,
                    category_name=event.event.category_name
                ),
                EventType.CHANNEL_UPDATE,
            ),
            id=f"on-channel-update-{event.event.broadcaster_user_id}",
            task_queue=MAIN_QUEUE
        )

    async def on_stream_online(self, event: StreamOnlineEvent):
        client = await get_client()

        await client.start_workflow(
            OnStreamOnlineWorkflow.run,
            args=(
                int(event.event.broadcaster_user_id),
                EventType.STREAM_ONLINE
            ),
            id=f"on-stream-online-{event.event.broadcaster_user_id}",
            task_queue=MAIN_QUEUE
        )

    async def on_channel_points_custom_reward_redemption_add(
        self,
        event: ChannelPointsCustomRewardRedemptionAddEvent
    ):
        client = await get_client()

        await client.start_workflow(
            OnRewardRedemptionWorkflow.run,
            RewardRedemption.from_twitch_event(event),
            id=f"on-reward-redemption-{event.event.broadcaster_user_id}-{event.event.reward.id}",
            task_queue=MAIN_QUEUE
        )

    async def on_message(self, event: ChannelChatMessageEvent):
        client = await get_client()

        await client.start_workflow(
            OnMessageWorkflow.run,
            MessageEvent.from_twitch_event(
                self.streamer.twitch.name,
                event
            ),
            id=f"on-message-{event.event.broadcaster_user_id}-{event.event.message_id}",
            task_queue=MAIN_QUEUE
        )

    async def _clean_subs(self, method: str, streamer: StreamerConfig):
        match method:
            case "listen_channel_update_v2":
                sub_type = "channel.update"
            case "listen_stream_online":
                sub_type = "stream.online"
            case "listen_channel_chat_message":
                sub_type = "channel.chat.message"
            case "listen_channel_points_custom_reward_redemption_add":
                sub_type = "channel.channel_points_custom_reward_redemption.add"
            case _:
                raise ValueError("Unknown method")

        subs = await self.twitch.get_eventsub_subscriptions(
            user_id=str(streamer.twitch.id)
        )

        for sub in subs.data:
            if sub.type == sub_type:
                try:
                    await self.twitch.delete_eventsub_subscription(sub.id)
                except Exception as e:
                    logger.error(f"Failed to delete subscription {sub.id}", exc_info=e)

    async def subscribe_with_retry(
            self,
            method: Literal["listen_channel_update_v2"]
                | Literal["listen_stream_online"]
                | Literal["listen_channel_chat_message"]
                | Literal["listen_channel_points_custom_reward_redemption_add"],
            eventsub: EventSubWebsocket,
            streamer: StreamerConfig,
            retry: int = 10
        ):
        await self._clean_subs(method, streamer)

        try:
            match method:
                case "listen_channel_update_v2":
                    await eventsub.listen_channel_update_v2(str(streamer.twitch.id), self.on_channel_update)
                case "listen_stream_online":
                    await eventsub.listen_stream_online(str(streamer.twitch.id), self.on_stream_online)
                case "listen_channel_points_custom_reward_redemption_add":
                    await eventsub.listen_channel_points_custom_reward_redemption_add(
                        str(streamer.twitch.id),
                        self.on_channel_points_custom_reward_redemption_add
                    )
                case "listen_channel_chat_message":
                    chatbot_in_chats = streamer.chatbot_in_chats or []

                    for chat_id in chatbot_in_chats:
                        await eventsub.listen_channel_chat_message(
                            str(chat_id),
                            str(streamer.twitch.id),
                            self.on_message
                        )
                case _:
                    raise ValueError("Unknown method")

            return
        except Exception as e:
            if retry <= 0:
                raise e

        await sleep(1)
        await self.subscribe_with_retry(method, eventsub, streamer, retry - 1)

    async def subscribe_to_streamer(self, eventsub: EventSubWebsocket, streamer: StreamerConfig):
        logger.info(f"Subscribe to events for {streamer.twitch.name}")
        await gather(
            self.subscribe_with_retry("listen_channel_update_v2", eventsub, streamer),
            self.subscribe_with_retry("listen_stream_online", eventsub, streamer),
            self.subscribe_with_retry("listen_channel_points_custom_reward_redemption_add", eventsub, streamer),
            self.subscribe_with_retry("listen_channel_chat_message", eventsub, streamer),
        )
        logger.info(f"Subscribe to events for {streamer.twitch.name} done")

    async def _check_token(self):
        assert self.twitch._user_auth_token is not None

        while True:
            for _ in range(60):
                if self.failed:
                    return

                await sleep(1)

            logger.info("Check token...")
            val_result = await validate_token(
                self.twitch._user_auth_token,
                auth_base_url=self.twitch.auth_base_url
            )
            if val_result.get('status', 200) != 200:
                await self.twitch.refresh_used_token()
                logger.info("Token refreshed")

    async def run(self) -> None:
        eventsub = EventSubWebsocket(twitch=self.twitch)

        try:
            eventsub.start()

            logger.info("Subscribe to events...")
            await self.subscribe_to_streamer(eventsub, self.streamer)
            logger.info("Twitch service started")

            await self._check_token()
        finally:
            logger.info("Twitch service stopping...")
            await eventsub.stop()

    @classmethod
    async def _start_for_streamer(cls, streamer: StreamerConfig):
        try:
            twith = await authorize(streamer.twitch.name, auto_refresh_auth=True)
            await cls(twith, streamer).run()
        except Exception as e:
            logger.error("Twitch service failed", exc_info=e)

    @classmethod
    async def start(cls):
        logger.info("Starting Twitch service...")

        streamers = await StreamerConfigRepository.all()

        await wait(
            [
                create_task(cls._start_for_streamer(streamer))
                for streamer in streamers
            ],
            return_when=FIRST_COMPLETED
        )

        await gather(
            *[cls._start_for_streamer(streamer) for streamer in streamers]
        )

        logger.info("Twitch service stopped")
