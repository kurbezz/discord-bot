import json

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class TwitchConfig(BaseModel):
    CHANNEL_ID: str
    CHANNEL_NAME: str


class DiscordConfig(BaseModel):
    GUILD_ID: int
    CHANNEL_ID: int

    GAME_LIST_CHANNEL_ID: int
    GAME_LIST_MESSAGE_ID: int


class StreamerConfig(BaseModel):
    TWITCH: TwitchConfig
    DISCORD: DiscordConfig | None = None
    TELEGRAM_CHANNEL_ID: int | None = None

    START_STREAM_MESSAGE: str | None = None
    CHANGE_CATEGORY_MESSAGE: str | None = None


class Config(BaseSettings):
    DISCORD_BOT_TOKEN: str
    DISCORD_BOT_ID: str
    DISCORD_BOT_ACTIVITY: str

    TELEGRAM_BOT_TOKEN: str

    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str

    TWITCH_ADMIN_USER_ID: str

    TWITCH_CALLBACK_URL: str
    TWITCH_CALLBACK_PORT: int = 80

    STREAMERS: list[StreamerConfig] = []

    SECRETS_FILE_PATH: str


    @field_validator("STREAMERS", mode="before")
    def check_streamers(cls, value):
        if isinstance(value, str):
            return json.loads(value)

        return value


config = Config()  # type: ignore
