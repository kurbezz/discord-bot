from asyncio import Lock
import json

from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope

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
    SCOPES = [AuthScope.CHANNEL_BOT]

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

    @classmethod
    async def run(cls):
        pass

    @classmethod
    async def start(cls):
        twith = await cls.authorize()

        await cls(twith).run()


async def start_twitch_service():
    await TwitchService.start()
