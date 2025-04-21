from domain.streamers import StreamerConfig

from .base import BaseRepository


class StreamerConfigRepository(BaseRepository):
    COLLECTION_NAME = "streamers"

    @classmethod
    async def get_by_twitch_id(cls, twitch_id: int) -> StreamerConfig:
        async with cls.connect() as collection:
            doc = await collection.find_one({"twitch.id": twitch_id})
            if doc is None:
                raise ValueError(f"Streamer with twitch id {twitch_id} not found")

            return StreamerConfig(**doc)

    @classmethod
    async def find_one(
        cls,
        integration_discord_guild_id: int | None = None,
        integration_discord_games_list_channel_id: int | None = None,
    ) -> StreamerConfig | None:
        filters = {}

        if integration_discord_guild_id is not None:
            filters["integrations.discord.guild_id"] = integration_discord_guild_id

        if integration_discord_games_list_channel_id is not None:
            filters[
                "integrations.discord.games_list.channel_id"
            ] = integration_discord_games_list_channel_id

        async with cls.connect() as collection:
            doc = await collection.find_one(filters)
            if doc is None:
                return None

            return StreamerConfig(**doc)

    @classmethod
    async def all(cls) -> list[StreamerConfig]:
        async with cls.connect() as collection:
            cursor = await collection.find()
            return [StreamerConfig(**doc) async for doc in cursor]
