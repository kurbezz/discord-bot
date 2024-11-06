import tomllib

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class TwitchConfig(BaseModel):
    id: int
    name: str

class NotificationsConfig(BaseModel):
    start_stream: str
    change_category: str | None = None

class GamesListConfig(BaseModel):
    channel_id: int
    message_id: int

class DiscordConfig(BaseModel):
    guild_id: int
    notifications_channel_id: int
    games_list: GamesListConfig | None = None
    roles: dict[str, int] | None = None

class TelegramConfig(BaseModel):
    notifications_channel_id: int

class IntegrationsConfig(BaseModel):
    discord: DiscordConfig | None = None
    telegram: TelegramConfig | None = None

class StreamerConfig(BaseModel):
    twitch: TwitchConfig
    notifications: NotificationsConfig
    integrations: IntegrationsConfig


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
        config_dir = Path("/app/configs")
        streamers = []
        for toml_file in config_dir.glob("*.toml"):
            if toml_file.is_file():
                with open(toml_file, "rb") as f:
                    streamer_config = tomllib.load(f)
                streamers.append(StreamerConfig(**streamer_config))
        return streamers if streamers else value


config = Config()  # type: ignore
