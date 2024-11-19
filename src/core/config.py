from pydantic import BaseModel
from pydantic_settings import BaseSettings

from httpx import Client


class Settings(BaseSettings):
    VAULT_HOST: str
    VAULT_SECRET_PATH: str
    VAULT_TOKEN: str


class Config(BaseModel):
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

    REDIS_URI: str


def get_config() -> Config:
    settings = Settings()  # type: ignore

    with Client() as client:
        response = client.get(
            f"https://{settings.VAULT_HOST}/v1/{settings.VAULT_SECRET_PATH}",
            headers={
                "X-Vault-Token": settings.VAULT_TOKEN,
                "Content-Type": "application/json",
            }
        )

        response.raise_for_status()

    return Config(**response.json()["data"]["data"])


config = get_config()
