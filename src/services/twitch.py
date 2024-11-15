from asyncio import Lock, sleep
from datetime import datetime
import json
import logging

from twitchAPI.helper import first
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.object.eventsub import StreamOnlineEvent, ChannelUpdateEvent

import aiofiles

from config import config, StreamerConfig
from services.notification import notify
from services.twitch_state import State


logger = logging.getLogger(__name__)


class TokenStorage:
    lock = Lock()

    @staticmethod
    async def save(acceess_token: str, refresh_token: str):
        data = json.dumps({"access_token": acceess_token, "refresh_token": refresh_token})

        async with TokenStorage.lock:
            async with aiofiles.open(config.SECRETS_FILE_PATH, "w") as f:
                await f.write(data)

    @staticmethod
    async def get() -> tuple[str, str]:
        async with TokenStorage.lock:
            async with aiofiles.open(config.SECRETS_FILE_PATH, "r") as f:
                data_str = await f.read()

        data = json.loads(data_str)
        return data["access_token"], data["refresh_token"]


class TwitchService:
    lock = Lock()

    SCOPES = [
        AuthScope.CHAT_READ,
        AuthScope.CHAT_EDIT,
    ]

    ONLINE_NOTIFICATION_DELAY = 15 * 60
    UPDATE_DELAY = 5 * 60

    def __init__(self, twitch: Twitch):
        self.twitch = twitch

        self.state: dict[int, State | None] = {}

    @classmethod
    async def authorize(cls):
        twitch = Twitch(
            config.TWITCH_CLIENT_ID,
            config.TWITCH_CLIENT_SECRET
        )

        twitch.user_auth_refresh_callback = TokenStorage.save

        token, refresh_token = await TokenStorage.get()
        await twitch.set_user_authentication(token, cls.SCOPES, refresh_token)

        await twitch.authenticate_app(cls.SCOPES)

        return twitch

    def get_streamer_config(self, streamer_id: int) -> StreamerConfig:
        for streamer in config.STREAMERS:
            if streamer.twitch.id == streamer_id:
                return streamer

        raise ValueError(f"Streamer with id {streamer_id} not found")

    async def notify_online(self, streamer_id: int):
        current_state = self.state.get(streamer_id)
        if current_state is None:
            raise RuntimeError("State is None")

        streamer = self.get_streamer_config(streamer_id)

        if streamer.notifications.start_stream is None:
            return

        await notify("start", streamer, current_state)

    async def notify_change_category(self, streamer_id: int):
        current_state = self.state.get(streamer_id)

        if current_state is None:
            raise RuntimeError("State is None")

        if (datetime.now() - current_state.last_live_at).seconds >= self.ONLINE_NOTIFICATION_DELAY:
            return

        streamer = self.get_streamer_config(streamer_id)

        if streamer.notifications.change_category is None:
            return

        await notify("change_category", streamer, current_state)

    async def get_current_stream(self, streamer_id: int, retry_count: int = 5, delay: int = 5):
        remain_retry = retry_count

        while remain_retry > 0:
            stream = await first(self.twitch.get_streams(user_id=[str(streamer_id)]))

            if stream is not None:
                return stream

            remain_retry -= 1
            await sleep(delay)

        return None

    async def on_channel_update(self, event: ChannelUpdateEvent):
        brodcaster_id = int(event.event.broadcaster_user_id)

        stream = await self.get_current_stream(brodcaster_id)
        if stream is None:
            return

        async with self.lock:
            current_state = self.state.get(brodcaster_id)
            if current_state is None:
                return

            changed = current_state.category != event.event.category_name

            current_state.title = event.event.title
            current_state.category = event.event.category_name
            current_state.last_live_at = datetime.now()

            self.state[brodcaster_id] = current_state

        if changed:
            await self.notify_change_category(brodcaster_id)

    async def _on_stream_online(self, streamer_id: int):
        current_stream = await self.get_current_stream(streamer_id)
        if current_stream is None:
            return

        state = State(
            title=current_stream.title,
            category=current_stream.game_name,
            last_live_at=datetime.now()
        )

        async with self.lock:
            current_state = self.state.get(streamer_id)

            is_need_notify = current_state is None or (datetime.now() - current_state.last_live_at).seconds >= self.ONLINE_NOTIFICATION_DELAY

            self.state[streamer_id] = state

        if is_need_notify:
            await self.notify_online(streamer_id)

    async def on_stream_online(self, event: StreamOnlineEvent):
        await self._on_stream_online(int(event.event.broadcaster_user_id))

    async def run(self):
        eventsub = EventSubWebhook(
            callback_url=config.TWITCH_CALLBACK_URL,
            port=config.TWITCH_CALLBACK_PORT,
            twitch=self.twitch,
            message_deduplication_history_length=50
        )

        for streamer in config.STREAMERS:
            current_stream = await self.get_current_stream(streamer.twitch.id)

            if current_stream:
                self.state[streamer.twitch.id] = State(
                    title=current_stream.title,
                    category=current_stream.game_name,
                    last_live_at=datetime.now()
                )
            else:
                self.state[streamer.twitch.id] = None

        try:
            await eventsub.unsubscribe_all()

            eventsub.start()

            logger.info("Subscribe to events...")

            for streamer in config.STREAMERS:
                logger.info(f"Subscribe to events for {streamer.twitch.name}")
                await eventsub.listen_channel_update_v2(str(streamer.twitch.id), self.on_channel_update)
                await eventsub.listen_stream_online(str(streamer.twitch.id), self.on_stream_online)
                logger.info(f"Subscribe to events for {streamer.twitch.name} done")

            logger.info("Twitch service started")

            while True:
                await sleep(self.UPDATE_DELAY)

                for streamer in config.STREAMERS:
                    await self._on_stream_online(streamer.twitch.id)
        finally:
            await eventsub.stop()
            await self.twitch.close()

            raise RuntimeError("Twitch service stopped")

    @classmethod
    async def start(cls):
        logger.info("Starting Twitch service...")

        twith = await cls.authorize()
        await cls(twith).run()


async def start_twitch_service():
    await TwitchService.start()
