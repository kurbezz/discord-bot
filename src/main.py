from asyncio import gather
import logging

from services.discord import start_discord_sevice
from services.twitch import start_twitch_service


logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting services...")
    await gather(
        start_discord_sevice(),
        start_twitch_service()
    )


if __name__ == "__main__":
    from asyncio import run

    run(main())
