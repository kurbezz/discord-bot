from asyncio import sleep, gather
from datetime import datetime, timezone
import logging
from typing import NoReturn, Literal

from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.object.eventsub import StreamOnlineEvent, ChannelUpdateEvent
from twitchAPI.oauth import validate_token

from core.config import config
from repositories.streamers import StreamerConfigRepository, StreamerConfig
from modules.stream_notifications.tasks import on_stream_state_change, check_streams_states

from .authorize import authorize
from ..state import State


logger = logging.getLogger(__name__)


class TwitchService:
    ONLINE_NOTIFICATION_DELAY = 15 * 60

    def __init__(self, twitch: Twitch):
        self.twitch = twitch

        self.failed = False

    async def on_channel_update(self, event: ChannelUpdateEvent):
        try:
            stream = await first(self.twitch.get_streams(user_id=[event.event.broadcaster_user_id]))
        except RuntimeError as e:
            await check_streams_states.kiq()
            self.failed = True
            raise e

        if stream is None:
            return

        await on_stream_state_change.kiq(
            int(event.event.broadcaster_user_id),
            State(
                title=event.event.title,
                category=event.event.category_name,
                last_live_at=datetime.now(timezone.utc)
            )
        )

    async def on_stream_online(self, event: StreamOnlineEvent):
        await on_stream_state_change.kiq(int(event.event.broadcaster_user_id))

    async def subscribe_with_retry(
            self,
            method: Literal["listen_channel_update_v2"] | Literal["listen_stream_online"],
            eventsub: EventSubWebhook,
            streamer: StreamerConfig,
            retry: int = 10
        ):

        try:
            if method == "listen_channel_update_v2":
                await eventsub.listen_channel_update_v2(str(streamer.twitch.id), self.on_channel_update)
            elif method == "listen_stream_online":
                await eventsub.listen_stream_online(str(streamer.twitch.id), self.on_stream_online)
            else:
                raise ValueError("Unknown method")

            return
        except Exception as e:
            if retry <= 0:
                raise e

        if method == "listen_channel_update_v2":
            sub_type = "channel.update"
        elif method == "listen_stream_online":
            sub_type = "stream.online"
        else:
            raise ValueError("Unknown method")

        subs = await self.twitch.get_eventsub_subscriptions(
            user_id=str(streamer.twitch.id)
        )

        for sub in subs.data:
            if sub.type == sub_type:
                await self.twitch.delete_eventsub_subscription(sub.id)

        await sleep(1)
        await self.subscribe_with_retry(method, eventsub, streamer, retry - 1)

    async def subscribe_to_streamer(self, eventsub: EventSubWebhook, streamer: StreamerConfig):
        logger.info(f"Subscribe to events for {streamer.twitch.name}")
        await gather(
            self.subscribe_with_retry("listen_channel_update_v2", eventsub, streamer),
            self.subscribe_with_retry("listen_stream_online", eventsub, streamer)
        )
        logger.info(f"Subscribe to events for {streamer.twitch.name} done")

    async def _check_token(self):
        assert self.twitch._user_auth_token is not None

        while not self.failed:
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

    async def stop(self, eventsub: EventSubWebhook):
        self.failed = True

        try:
            await eventsub.stop()
        except Exception as e:
            logger.error(e)

        try:
            await self.twitch.close()
        except Exception as e:
            logger.error(e)

    async def run(self) -> NoReturn:
        eventsub = EventSubWebhook(
            callback_url=config.TWITCH_CALLBACK_URL,
            port=config.TWITCH_CALLBACK_PORT,
            twitch=self.twitch,
            message_deduplication_history_length=50
        )
        eventsub.wait_for_subscription_confirm_timeout = 60

        streamers = await StreamerConfigRepository.all()

        try:
            eventsub.start()

            logger.info("Subscribe to events...")
            await gather(
                *[self.subscribe_to_streamer(eventsub, streamer) for streamer in streamers]
            )
            logger.info("Twitch service started")

            await self._check_token()
        finally:
            logger.info("Twitch service stopping...")
            await self.stop(eventsub)

    @classmethod
    async def start(cls):
        logger.info("Starting Twitch service...")

        twith = await authorize(auto_refresh_auth=True)
        await cls(twith).run()

        logger.info("Twitch service stopped")


async def start_twitch_service() -> NoReturn:
    await TwitchService.start()
