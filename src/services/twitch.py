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

from pydantic import BaseModel

from config import config, StreamerConfig
from services.notification import notify


logger = logging.getLogger(__name__)


class State(BaseModel):
    title: str
    category: str

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

    ONLINE_NOTIFICATION_DELAY = 15 * 60
    UPDATE_DELAY = 5 * 60

    def __init__(self, twitch: Twitch):
        self.twitch = twitch

        self.state: dict[str, State | None] = {}

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

    def get_streamer_config(self, streamer_id: str) -> StreamerConfig:
        for streamer in config.STREAMERS:
            if streamer.TWITCH.CHANNEL_ID == streamer_id:
                return streamer

        raise ValueError(f"Streamer with id {streamer_id} not found")

    async def notify_online(self, streamer_id: str):
        current_state = self.state.get(streamer_id)
        if current_state is None:
            raise RuntimeError("State is None")

        streamer = self.get_streamer_config(streamer_id)

        if streamer.START_STREAM_MESSAGE is None:
            return

        msg = streamer.START_STREAM_MESSAGE.replace("\\n", "\n").format(
            title=current_state.title,
            category=current_state.category
        )

        await notify(msg, streamer)

    async def notify_change_category(self, streamer_id: str):
        current_state = self.state.get(streamer_id)

        if current_state is None:
            raise RuntimeError("State is None")

        if (datetime.now() - current_state.last_live_at).seconds > 60:
            raise RuntimeError("State is not live")

        streamer = self.get_streamer_config(streamer_id)

        if streamer.CHANGE_CATEGORY_MESSAGE is None:
            return

        msg = streamer.CHANGE_CATEGORY_MESSAGE.replace("\\n", "\n").format(
            category=current_state.category
        )

        await notify(msg, streamer)

    async def get_current_stream(self, streamer_id: str, retry_count: int = 5, delay: int = 5):
        remain_retry = retry_count

        while remain_retry > 0:
            stream = await first(self.twitch.get_streams(user_id=[streamer_id]))

            if stream is not None:
                return stream

            remain_retry -= 1
            await sleep(delay)

        return None

    async def on_channel_update(self, event: ChannelUpdateEvent):
        brodcaster_id = event.event.broadcaster_user_id

        stream = await self.get_current_stream(brodcaster_id)
        if stream is None:
            return

        current_state = self.state.get(brodcaster_id)
        if current_state is None:
            return

        changed = current_state.category == event.event.category_name

        current_state.title = event.event.title
        current_state.category = event.event.category_name
        current_state.last_live_at = datetime.now()

        self.state[brodcaster_id] = current_state

        if changed:
            await self.notify_change_category(brodcaster_id)

    async def _on_stream_online(self, streamer_id: str):
        current_stream = await self.get_current_stream(streamer_id)
        if current_stream is None:
            return

        state = State(
            title=current_stream.title,
            category=current_stream.game_name,
            last_live_at=datetime.now()
        )

        current_state = self.state.get(streamer_id)

        if current_state is None or (datetime.now() - current_state.last_live_at).seconds >= self.ONLINE_NOTIFICATION_DELAY:
            await self.notify_online(streamer_id)

        self.state[streamer_id] = state

    async def on_stream_online(self, event: StreamOnlineEvent):
        await self._on_stream_online(event.event.broadcaster_user_id)

    async def run(self):
        eventsub = EventSubWebhook(
            callback_url=config.TWITCH_CALLBACK_URL,
            port=config.TWITCH_CALLBACK_PORT,
            twitch=self.twitch,
            message_deduplication_history_length=50
        )

        for streamer in config.STREAMERS:
            current_stream = await self.get_current_stream(streamer.TWITCH.CHANNEL_ID)
            if current_stream:
                self.state[streamer.TWITCH.CHANNEL_ID] = State(
                    title=current_stream.title,
                    category=current_stream.game_name,
                    last_live_at=datetime.now()
                )
            else:
                self.state[streamer.TWITCH.CHANNEL_ID] = None

        try:
            await eventsub.unsubscribe_all()

            eventsub.start()

            logger.info("Subscribe to events...")

            for streamer in config.STREAMERS:
                await eventsub.listen_channel_update_v2(streamer.TWITCH.CHANNEL_ID, self.on_channel_update)
                await eventsub.listen_stream_online(streamer.TWITCH.CHANNEL_ID, self.on_stream_online)

            logger.info("Twitch service started")

            while True:
                await sleep(self.UPDATE_DELAY)

                for streamer in config.STREAMERS:
                    await self._on_stream_online(streamer.TWITCH.CHANNEL_ID)
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
