from asyncio import sleep
import logging
from typing import NoReturn

from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.object.eventsub import StreamOnlineEvent, ChannelUpdateEvent

from core.config import config
from repositories.streamers import StreamerConfigRepository
from modules.stream_notifications.tasks import on_stream_state_change

from .authorize import authorize


logger = logging.getLogger(__name__)


class TwitchService:
    ONLINE_NOTIFICATION_DELAY = 15 * 60

    def __init__(self, twitch: Twitch):
        self.twitch = twitch

    async def on_channel_update(self, event: ChannelUpdateEvent):
        await on_stream_state_change.kiq(int(event.event.broadcaster_user_id))

    async def on_stream_online(self, event: StreamOnlineEvent):
        await on_stream_state_change.kiq(int(event.event.broadcaster_user_id))

    async def run(self) -> NoReturn:
        eventsub = EventSubWebhook(
            callback_url=config.TWITCH_CALLBACK_URL,
            port=config.TWITCH_CALLBACK_PORT,
            twitch=self.twitch,
            message_deduplication_history_length=50
        )

        streamers = await StreamerConfigRepository.all()

        try:
            await eventsub.unsubscribe_all()

            eventsub.start()

            logger.info("Subscribe to events...")

            for streamer in streamers:
                logger.info(f"Subscribe to events for {streamer.twitch.name}")
                await eventsub.listen_channel_update_v2(str(streamer.twitch.id), self.on_channel_update)
                await eventsub.listen_stream_online(str(streamer.twitch.id), self.on_stream_online)
                logger.info(f"Subscribe to events for {streamer.twitch.name} done")

            logger.info("Twitch service started")

            while True:
                await sleep(0.1)
        finally:
            await eventsub.stop()
            await self.twitch.close()

            raise RuntimeError("Twitch service stopped")

    @classmethod
    async def start(cls):
        logger.info("Starting Twitch service...")

        twith = await authorize(auto_refresh_auth=True)
        await cls(twith).run()


async def start_twitch_service() -> NoReturn:
    await TwitchService.start()
