from pydantic.env_settings import BaseSettings


class Config(BaseSettings):
    DISCORD_BOT_TOKEN: str

    DISCORD_GUILD_ID: int
    DISCORD_CHANNEL_ID: int

    DISCORD_BOT_ACTIVITY: str

    DISCORD_GAME_LIST_CHANNEL_ID: int
    DISCORD_GAME_LIST_MESSAGE_ID: int

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHANNEL_ID: int

    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str
    TWITCH_CHANNEL_ID: str


config = Config()
