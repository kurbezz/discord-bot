from asyncio import run

from applications.games_list.discord import client, logger
from core.config import config


async def start_discord_sevice():
    logger.info("Starting Discord service...")

    await client.start(config.DISCORD_BOT_TOKEN)


run(start_discord_sevice())
