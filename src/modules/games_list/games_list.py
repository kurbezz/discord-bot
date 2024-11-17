from typing import Self
from datetime import datetime

from discord import app_commands
from pydantic import BaseModel

from core.mongo import mongo_manager


class GameItem(BaseModel):
    name: str
    customer: str
    date: str | None

    def __str__(self) -> str:
        if self.date is not None:
            return f"* {self.name} ({self.customer}) | {self.date}"
        else:
            return f"* {self.name} ({self.customer})"


class Category(BaseModel):
    name: str
    games: list[GameItem]


class GameList:
    COLLECTION_NAME = "games_list_data"

    CATEGORY_MAP = {
        "points": "Заказанные игры (за 12к)",
        "paids": "Проплачены 🤑 ",
        "gifts": "Подарки",
    }

    def __init__(self, twitch_id: int, data: list[Category]):
        self.twitch_id = twitch_id
        self.data = data

    @classmethod
    async def get(cls, twitch_id: int) -> Self | None:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[cls.COLLECTION_NAME]

            doc = await collection.find_one({"twitch_id": twitch_id})
            if doc is None:
                return None

            return cls(
                twitch_id,
                [
                    Category(**category)
                    for category in doc["data"]
                ]
            )

    async def save(self):
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[self.COLLECTION_NAME]

            await collection.replace_one(
                {"twitch_id": self.twitch_id},
                {
                    "twitch_id": self.twitch_id,
                    "data": [category.model_dump() for category in self.data]
                },
                upsert=True
            )

    def add_game(self, category: str, game_item: GameItem):
        _category = self.CATEGORY_MAP.get(category)

        if game_item.date is None:
            game_item.date = datetime.now().strftime("%d.%m.%Y")

        for category_item in self.data:
            if category_item.name == _category:
                category_item.games.append(game_item)

    def delete_game(self, game_name: str):
        for category in self.data:
            for game in category.games:
                if game.name.startswith(game_name):
                    category.games.remove(game)

    def get_choices(self, query: str) -> list[app_commands.Choice[str]]:
        choices = []

        for category in self.data:
            for game in category.games:
                if query.lower() in game.name.lower():
                    choices.append(app_commands.Choice(name=game.name, value=game.name))

        return choices[:25]

    def __str__(self) -> str:
        result = ""

        for category in self.data:
            result += f"{category.name}:\n"

            for game in category.games:
                result += f"{game}\n"

            result += "\n\n"

        return result
