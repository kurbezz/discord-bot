from asyncio import Lock, sleep
from datetime import datetime
import json
import logging

from twitchAPI.helper import first
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent, ChannelUpdateEvent

import aiofiles

from pydantic import BaseModel

from config import config
from services.notification import notify


logger = logging.getLogger(__name__)


class State(BaseModel):
    title: str
    category: str
    is_live: bool
    last_live_at: datetime


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
    SCOPES = [
        AuthScope.CHAT_READ,
        AuthScope.CHAT_EDIT,
    ]

    ONLINE_NOTIFICATION_DELAY = 10 * 60

    def __init__(self, twitch: Twitch):
        self.twitch = twitch

        self.state: State | None = None

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

    async def notify_online(self):
        if self.state is None:
            raise RuntimeError("State is None")

        msg = f"HafMC сейчас стримит {self.state.title} ({self.state.category})! \nПрисоединяйся: https://twitch.tv/hafmc"

        await notify(msg)

    async def notify_change_category(self):
        if self.state is None:
            raise RuntimeError("State is None")

        msg = f"HafMC начал играть в {self.state.category}! \nПрисоединяйся: https://twitch.tv/hafmc"

        await notify(msg)

    async def get_current_stream(self, retry_count: int = 5, delay: int = 5):
        remain_retry = retry_count

        while remain_retry > 0:
            stream = await first(self.twitch.get_streams(user_id=[config.TWITCH_CHANNEL_ID]))

            if stream is not None:
                return stream

            remain_retry -= 1
            await sleep(delay)

        return None

    async def on_channel_update(self, event: ChannelUpdateEvent):
        if self.state is None:
            return

        if self.state.category == event.event.category_name:
            return

        self.state.title = event.event.title
        self.state.category = event.event.category_name
        self.state.last_live_at = datetime.now()

        await self.notify_change_category()

    async def _on_stream_online(self):
        current_stream = await self.get_current_stream()
        if current_stream is None:
            return

        state = State(
            title=current_stream.title,
            category=current_stream.game_name,
            is_live=True,
            last_live_at=datetime.now()
        )

        if self.state is None:
            self.state = state
            await self.notify_online()

        if (datetime.now() - self.state.last_live_at).seconds >= self.ONLINE_NOTIFICATION_DELAY:
            await self.notify_online()

        self.state = state

    async def on_stream_online(self, event: StreamOnlineEvent):
        await self._on_stream_online()

    async def on_stream_offline(self, event: StreamOfflineEvent):
        if self.state:
            self.state.is_live = False
            self.last_live_at = datetime.now()

    async def run(self):
        eventsub = EventSubWebhook(
            callback_url=config.TWITCH_CALLBACK_URL,
            port=config.TWITCH_CALLBACK_PORT,
            twitch=self.twitch,
            message_deduplication_history_length=50
        )

        current_stream = await self.get_current_stream()
        if current_stream:
            self.state = State(
                title=current_stream.title,
                category=current_stream.game_name,
                is_live=current_stream.type == "live",
                last_live_at=datetime.now()
            )

        try:
            await eventsub.unsubscribe_all()

            eventsub.start()

            logger.info("Subscribe to events...")

            await eventsub.listen_channel_update_v2(config.TWITCH_CHANNEL_ID, self.on_channel_update)
            await eventsub.listen_stream_online(config.TWITCH_CHANNEL_ID, self.on_stream_online)
            await eventsub.listen_stream_offline(config.TWITCH_CHANNEL_ID, self.on_stream_offline)

            logger.info("Twitch service started")

            while True:
                await sleep(5 * 60)
                await self._on_stream_online()
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
