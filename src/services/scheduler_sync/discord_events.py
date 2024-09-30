from typing import Self
from datetime import datetime, timedelta
import logging

from httpx import AsyncClient
from pydantic import BaseModel, field_serializer, SerializationInfo

from config import config

from services.scheduler_sync.twitch_events import TwitchEvent


logger = logging.getLogger(__name__)


class RecurrenceRule(BaseModel):
    start: datetime
    by_weekday: list[int]
    interval: int
    frequency: int

    @field_serializer("start", when_used="always")
    def serialize_datetime(self, value: datetime, info: SerializationInfo) -> str:
        return value.isoformat()

    def next_date(self, start: datetime) -> datetime:
        next_date = start

        while True:
            next_date += timedelta(days=1)

            if next_date <= datetime.now(start.tzinfo):
                continue

            if next_date.weekday() in self.by_weekday:
                return next_date


class DiscordEvent(BaseModel):
    id: str
    name: str
    description: str
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    recurrence_rule: RecurrenceRule | None
    creator_id: str


async def get_discord_events(guild_id: int) -> list[DiscordEvent]:
    async with AsyncClient() as client:
        response = await client.get(
            f"https://discord.com/api/v10/guilds/{guild_id}/scheduled-events",
            headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"}
        )

        response.raise_for_status()

        events = [DiscordEvent(**event) for event in response.json()]

        return [event for event in events if event.creator_id == config.DISCORD_BOT_ID]


async def delete_discord_event(guild_id: int, event_id: str):
    async with AsyncClient() as client:
        response = await client.delete(
            f"https://discord.com/api/v10/guilds/{guild_id}/scheduled-events/{event_id}",
            headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"}
        )

        response.raise_for_status()
        return response.json()


class EntityMetadata(BaseModel):
    location: str


class CreateDiscordEvent(BaseModel):
    name: str
    description: str
    privacy_level: int
    entity_type: int
    entity_metadata: EntityMetadata
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    recurrence_rule: RecurrenceRule | None

    @field_serializer("scheduled_start_time", "scheduled_end_time", when_used="always")
    def serialize_datetime(self, value: datetime, info: SerializationInfo) -> str:
        return value.isoformat()

    @classmethod
    def parse_from_twitch_event(cls, event: TwitchEvent, channel_name: str) -> Self:
        if event.categories:
            name = f"{event.name} | {event.categories}"
        else:
            name = event.name

        if event.repeat_rule:
            recurrence_rule = RecurrenceRule(
                start=event.start_at,
                by_weekday=[event.repeat_rule.weekday.get_number()],
                interval=1,
                frequency=2
            )
        else:
            recurrence_rule = None

        return cls(
            name=name,
            description=f"{event.description or ''}\n\n\n\n#{event.uid}",
            privacy_level=2,
            entity_type=3,
            entity_metadata=EntityMetadata(location=f"https://twitch.tv/{channel_name}"),
            scheduled_start_time=event.start_at,
            scheduled_end_time=event.end_at,
            recurrence_rule=recurrence_rule
        )


async def create_discord_event(guild_id: int, event: CreateDiscordEvent):
    async with AsyncClient() as client:
        response = await client.post(
            f"https://discord.com/api/v10/guilds/{guild_id}/scheduled-events",
            json=event.model_dump(),
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            raise ValueError(response.json())

        return response.json()


class UpdateDiscordEvent(BaseModel):
    name: str
    description: str
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    recurrence_rule: RecurrenceRule | None

    @field_serializer("scheduled_start_time", "scheduled_end_time", when_used="always")
    def serialize_datetime(self, value: datetime, info: SerializationInfo) -> str:
        return value.isoformat()


async def edit_discord_event(guild_id: int, event_id: str, event: UpdateDiscordEvent):
    async with AsyncClient() as client:
        response = await client.patch(
            f"https://discord.com/api/v10/guilds/{guild_id}/scheduled-events/{event_id}",
            json=event.model_dump(),
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code != 200:
            raise ValueError(response.json())

        return response.json()
