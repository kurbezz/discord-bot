from asyncio import gather

from services.discord import start_discord_sevice
from services.twitch import start_twitch_service


async def main():
    print("Starting services...")
    await gather(
        start_discord_sevice(),
        start_twitch_service()
    )


if __name__ == "__main__":
    from asyncio import run

    run(main())
