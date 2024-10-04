import logging

from httpx import AsyncClient

from config import config, StreamerConfig


logger = logging.getLogger(__name__)


async def notify_telegram(msg: str, chat_id: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": msg,
            }
        )


async def notify_discord(msg: str, channel_id: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"
            },
            json={
                "content": msg,
            }
        )


async def notify(msg: str, streamer_config: StreamerConfig):
    integrations = streamer_config.integrations

    if (discord := integrations.discord) is not None:
        if discord.notifications_channel_id is not None:
            try:
                await notify_discord(msg, str(discord.notifications_channel_id))
            except Exception as e:
                logger.error("Failed to notify discord", exc_info=e)

    if (telegram := integrations.telegram) is not None:
        if telegram.notifications_channel_id is not None:
            try:
                await notify_telegram(msg, str(telegram.notifications_channel_id))
            except Exception as e:
                logger.error("Failed to notify telegram", exc_info=e)
