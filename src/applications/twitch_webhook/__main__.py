from asyncio import run

from .twitch.webhook import TwitchService


async def start_twitch_service() -> None:
    await TwitchService.start()


run(start_twitch_service())
