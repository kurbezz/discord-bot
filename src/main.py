from asyncio import wait, create_task
import logging

from modules.games_list import start as start_games_list_module
from modules.stream_notifications import start as start_stream_notifications_module

from core.mongo import mongo_manager


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def main():
    logger.info("Starting services...")

    await mongo_manager.init()

    await wait([
        create_task(start_games_list_module()),
        create_task(start_stream_notifications_module())
    ], return_when="FIRST_COMPLETED")


if __name__ == "__main__":
    from asyncio import run

    run(main())
