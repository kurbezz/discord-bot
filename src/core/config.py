from pydantic_settings import BaseSettings


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

    MONGODB_URI: str

    SECRETS_FILE_PATH: str


config = Config()  # type: ignore
