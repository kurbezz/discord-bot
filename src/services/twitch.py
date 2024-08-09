from asyncio import Lock, sleep
import json
import uuid

from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.object.eventsub import ChannelChatMessageEvent, StreamOnlineEvent, StreamOfflineEvent

import aiofiles

from config import config


class State:
    pass


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

        return twitch

    async def on_channel_chat_message(self, event: ChannelChatMessageEvent):
        print("on_channel_chat_message", event)

    async def on_stream_online(self, event: StreamOnlineEvent):
        print("on_stream_online", event)

    async def on_stream_offline(self, event: StreamOfflineEvent):
        print("on_stream_offline", event)

    async def run(self):
        try:
            eventsub = EventSubWebhook(
                callback_url=config.TWITCH_CALLBACK_URL,
                port=config.TWITCH_CALLBACK_PORT,
                twitch=self.twitch,
                message_deduplication_history_length=50
            )

            await eventsub.unsubscribe_all()

            eventsub.start()

            await eventsub.listen_channel_chat_message(config.TWITCH_CHANNEL_ID, config.TWITCH_ADMIN_USER_ID, self.on_channel_chat_message)
            await eventsub.listen_stream_online(config.TWITCH_CHANNEL_ID, self.on_stream_online)
            await eventsub.listen_stream_offline(config.TWITCH_CHANNEL_ID, self.on_stream_offline)

            while True:
                await sleep(1)
        finally:
            await eventsub.stop()
            await self.twitch.close()

    @classmethod
    async def start(cls):
        print("Starting Twitch service...")

        twith = await cls.authorize()
        await cls(twith).run()


async def start_twitch_service():
    await TwitchService.start()
