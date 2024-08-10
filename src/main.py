from asyncio import wait, create_task
import logging

from services.discord import start_discord_sevice
from services.twitch import start_twitch_service
from services.scheduler_sync import start_synchronizer

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def main():
    logger.info("Starting services...")

    await wait([
        create_task(start_discord_sevice()),
        create_task(start_twitch_service()),
        # create_task(start_synchronizer())
    ], return_when="FIRST_COMPLETED")


if __name__ == "__main__":
    from asyncio import run

    run(main())
