import discord
from discord.abc import Messageable
from discord import Object
from discord import app_commands

from services.games_list import GameList, GameItem

from config import config


class DiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(config.DISCORD_BOT_ACTIVITY),
            status=discord.Status.online,
        )


client = DiscordClient()


@client.tree.command(guild=Object(id=config.DISCORD_GUILD_ID))
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
    if interaction.channel is None or interaction.channel.id != config.DISCORD_CHANNEL_ID:
        return

    if not isinstance(interaction.channel, Messageable):
        return

    game_list_message = await interaction.channel.fetch_message(config.DISCORD_GAME_LIST_MESSAGE_ID)

    game_list = GameList.parse(game_list_message.content)
    game_list.add_game(category, GameItem(name=game, customer=customer, date=date))

    await game_list_message.edit(content=str(game_list))


async def game_list_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    if not isinstance(interaction.channel, Messageable):
        return []

    game_list_message = await interaction.channel.fetch_message(config.DISCORD_GAME_LIST_MESSAGE_ID)

    game_list = GameList.parse(game_list_message.content)

    return game_list.get_choices(current)


@client.tree.command(guild=Object(id=config.DISCORD_GUILD_ID))
@app_commands.describe(game="Игра")
@app_commands.autocomplete(game=game_list_autocomplete)
async def delete(interaction: discord.Interaction, game: str):
    if interaction.channel is None or interaction.channel.id != config.DISCORD_CHANNEL_ID:
        return

    if not isinstance(interaction.channel, Messageable):
        return

    game_list_message = await interaction.channel.fetch_message(config.DISCORD_GAME_LIST_MESSAGE_ID)

    game_list = GameList.parse(game_list_message.content)
    game_list.delete_game(game)

    await game_list_message.edit(content=str(game_list))


async def start_discord_sevice():
    client.run(config.DISCORD_BOT_TOKEN)
