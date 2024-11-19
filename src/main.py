import logging
import sys

from modules.games_list import start as start_games_list_module
from modules.stream_notifications import start as start_stream_notifications_module

from core.mongo import mongo_manager
from core.redis import redis_manager


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def main():
    logger.info("Starting services...")

    if len(sys.argv) != 2:
        raise RuntimeError("Usage: python main.py <module>")

    module = sys.argv[1]

    await mongo_manager.init()
    await redis_manager.init()

    if module == "games_list":
        await start_games_list_module()
    elif module == "stream_notifications":
        await start_stream_notifications_module()
    else:
        raise RuntimeError(f"Unknown module: {module}")


if __name__ == "__main__":
    from asyncio import run

    run(main())
