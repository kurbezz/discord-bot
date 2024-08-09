from typing import Self
from datetime import datetime
import re

from discord import app_commands
from pydantic import BaseModel


class GameItem(BaseModel):
    name: str
    customer: str
    date: str | None

    def __str__(self) -> str:
        # set timezone to Moscow
        _date = self.date or datetime.now().strftime("%d.%m.%Y")
        return f"* {self.name} ({self.customer}) | {_date}"

    @classmethod
    def parse(cls, line: str) -> Self:
        regex_result = re.search(r"^\* (.+) \((.+)\) \| (.+)$", line)

        if regex_result is None:
            raise ValueError(f"Invalid game item: {line}")

        name, customer, date = regex_result.groups()

        return cls(name=name, customer=customer, date=date)


class Category(BaseModel):
    name: str
    games: list[GameItem]


class GameList:
    def __init__(self, data: list[Category]):
        self.data = data

    @classmethod
    def parse(cls, message: str) -> Self:
        categories = []

        for line in message.split("\n"):
            if line == "".strip():
                continue

            if not line.startswith("*"):
                name = line.replace(":", "")
                categories.append(Category(name=name, games=[]))
            else:
                categories[-1].games.append(GameItem.parse(line.strip()))

        return cls(data=categories)

    def add_game(self, category: str, game_item: GameItem):
        for category_item in self.data:
            if category_item.name == category:
                category_item.games.append(game_item)

    def delete_game(self, game_name: str):
        for category in self.data:
            for game in category.games:
                if game.name.startswith(game_name):
                    category.games.remove(game)

    def __str__(self) -> str:
        result = ""

        for category in self.data:
            result += f"{category.name}:\n"

            for game in category.games:
                result += f"{game}\n"

            result += "\n\n"

        return result

    def get_choices(self, query: str) -> list[app_commands.Choice[str]]:
        choices = []

        for category in self.data:
            for game in category.games:
                if query.lower() in game.name.lower():
                    choices.append(app_commands.Choice(name=game.name, value=game.name))

        return choices[:25]
