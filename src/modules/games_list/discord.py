import logging

import discord
from discord.abc import Messageable
from discord import Object
from discord import app_commands

from modules.games_list.games_list import GameList, GameItem

from core.config import config
from repositories.streamers import StreamerConfigRepository


logger = logging.getLogger(__name__)


async def get_game_list_channel_to_message_map() -> dict[int, int]:
    result = {}

    streamers = await StreamerConfigRepository.all()

    for streamer in streamers:
        if (integration := streamer.integrations.discord) is None:
            continue

        if (games_list := integration.games_list) is None:
            continue

        if games_list.channel_id is None or games_list.message_id is None:
            continue

        result[games_list.channel_id] = games_list.message_id

    return result


class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        streamers = await StreamerConfigRepository.all()

        for streamer in streamers:
            if (integration := streamer.integrations.discord) is None:
                continue

            if integration.games_list is None:
                continue

            self.tree.copy_global_to(guild=Object(id=integration.guild_id))
            await self.tree.sync(guild=Object(id=integration.guild_id))

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(config.DISCORD_BOT_ACTIVITY),
            status=discord.Status.online,
        )


client = DiscordClient()


@client.tree.command()
@app_commands.describe(
    category="Раздел",
    customer="Кто заказал",
    game="Игра",
    date="Дата заказа"
)
@app_commands.choices(
    category=[
        app_commands.Choice(name="Заказ за баллы", value="points"),
        app_commands.Choice(name="Проплачены", value="paids"),
        app_commands.Choice(name="Подарки", value="gifts"),
    ],
)
async def add(
    interaction: discord.Interaction,
    category: str,
    customer: str,
    game: str,
    date: str | None = None
):
    if not isinstance(interaction.channel, Messageable):
        await interaction.response.send_message(
            "Interation not allowed in this channel!", ephemeral=True
        )
        return

    streamer = await StreamerConfigRepository.find_one(
        integration_discord_guild_id=interaction.guild_id,
        integration_discord_games_list_channel_id=interaction.channel_id
    )

    if streamer is None:
        await interaction.response.send_message(
            "Interation not allowed in this channel!", ephemeral=True
        )
        return

    if streamer.integrations.discord is None or streamer.integrations.discord.games_list is None:
        await interaction.response.send_message(
            "Need setup!", ephemeral=True
        )
        return

    game_list = await GameList.get(streamer.twitch.id)
    if game_list is None:
        await interaction.response.send_message(
            "Game list not found!", ephemeral=True
        )
        return

    game_list.add_game(category, GameItem(name=game, customer=customer, date=date))

    game_list_message = await interaction.channel.fetch_message(
        streamer.integrations.discord.games_list.message_id
    )

    await game_list_message.edit(content=str(game_list))
    await game_list.save(streamer.twitch.id)

    await interaction.response.send_message("Игра добавлена!", ephemeral=True)


async def game_list_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    streamer = await StreamerConfigRepository.find_one(
        integration_discord_guild_id=interaction.guild_id,
        integration_discord_games_list_channel_id=interaction.channel_id
    )
    if streamer is None:
        return []

    game_list = await GameList.get(streamer.twitch.id)
    if game_list is None:
        return []

    return game_list.get_choices(current)


@client.tree.command()
@app_commands.describe(game="Игра")
@app_commands.autocomplete(game=game_list_autocomplete)
async def delete(interaction: discord.Interaction, game: str):
    if not isinstance(interaction.channel, Messageable):
        await interaction.response.send_message(
            "Interation not allowed in this channel!", ephemeral=True
        )
        return

    streamer = await StreamerConfigRepository.find_one(
        integration_discord_guild_id=interaction.guild_id,
        integration_discord_games_list_channel_id=interaction.channel_id
    )

    if streamer is None:
        await interaction.response.send_message(
            "Interation not allowed in this channel!", ephemeral=True
        )
        return

    if streamer.integrations.discord is None or streamer.integrations.discord.games_list is None:
        await interaction.response.send_message(
            "Need setup!", ephemeral=True
        )
        return

    game_list = await GameList.get(streamer.twitch.id)
    if game_list is None:
        await interaction.response.send_message(
            "Game list not found!", ephemeral=True
        )
        return

    game_list.delete_game(game)

    game_list_message = await interaction.channel.fetch_message(
        streamer.integrations.discord.games_list.message_id
    )

    await game_list_message.edit(content=str(game_list))
    await game_list.save(streamer.twitch.id)

    await interaction.response.send_message("Игра удалена!", ephemeral=True)


async def start_discord_sevice():
    logger.info("Starting Discord service...")

    await client.start(config.DISCORD_BOT_TOKEN)
