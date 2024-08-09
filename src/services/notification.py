from asyncio import gather

from httpx import AsyncClient

from config import config


async def notify_telegram(msg: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHANNEL_ID,
                "text": msg,
            }
        )


async def notify_discord(msg: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://discord.com/api/v10/channels/{config.DISCORD_CHANNEL_ID}/messages",
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"
            },
            json={
                "content": msg,
            }
        )


async def notify(msg: str):
    await gather(
        notify_telegram(msg),
        notify_discord(msg)
    )
