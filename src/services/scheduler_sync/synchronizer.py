from asyncio import sleep
import logging

from services.scheduler_sync.twitch_events import get_twitch_events, TwitchEvent
from services.scheduler_sync.discord_events import (
    get_discord_events, DiscordEvent,
    delete_discord_event,
    create_discord_event, CreateDiscordEvent,
    edit_discord_event, UpdateDiscordEvent
)
from services.scheduler_sync.comparators import compare

from config import config, TwitchConfig


logger = logging.getLogger(__name__)


async def add_events(
    guild_id: int,
    twitch_channel_name: str,
    twitch_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    discord_events_ids = [event[0] for event in discord_events]

    for (uid, event) in twitch_events:
        if uid not in discord_events_ids:
            create_event = CreateDiscordEvent.parse_from_twitch_event(event, twitch_channel_name)
            await create_discord_event(guild_id, create_event)


async def remove_events(
    guild_id: int,
    twith_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    twith_events_ids = [event[0] for event in twith_events]

    for (uid, event) in discord_events:
        if uid not in twith_events_ids:
            await delete_discord_event(guild_id, uid)


async def edit_events(
    guild_id: int,
    twitch_channel_name: str,
    twith_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    for (uid, twitch_event) in twith_events:
        for (discord_id, discord_event) in discord_events:
            if uid != discord_id:
                continue

            create_event = CreateDiscordEvent.parse_from_twitch_event(twitch_event, twitch_channel_name)

            if compare(create_event, discord_event):
                continue

            update_event = UpdateDiscordEvent(
                name=create_event.name,
                description=create_event.description,
                scheduled_start_time=create_event.scheduled_start_time,
                scheduled_end_time=create_event.scheduled_end_time,
                recurrence_rule=create_event.recurrence_rule
            )

            if update_event.recurrence_rule is not None:
                duration = update_event.scheduled_end_time - update_event.scheduled_start_time

                update_event.scheduled_start_time = update_event.recurrence_rule.next_date(update_event.scheduled_start_time)
                update_event.scheduled_end_time = update_event.scheduled_start_time + duration

                update_event.recurrence_rule.start = update_event.scheduled_start_time

            await edit_discord_event(guild_id, discord_event.id, update_event)


async def syncronize(twitch: TwitchConfig, discord_guild_id: int):
    twitch_events = await get_twitch_events(twitch.CHANNEL_ID)
    discord_events = await get_discord_events(discord_guild_id)

    twitch_events_with_id = [(event.uid, event) for event in twitch_events]
    discord_events_with_id = [
        (event.description.rsplit("#")[1], event)
        for event in discord_events
    ]

    await add_events(discord_guild_id, twitch.CHANNEL_NAME, twitch_events_with_id, discord_events_with_id)
    await remove_events(discord_guild_id, twitch_events_with_id, discord_events_with_id)
    await edit_events(discord_guild_id, twitch.CHANNEL_NAME, twitch_events_with_id, discord_events_with_id)


async def start_synchronizer():
    await sleep(5)

    while True:
        try:
            for streamer in config.STREAMERS:
                if streamer.DISCORD is None:
                    continue

                await syncronize(streamer.TWITCH, streamer.DISCORD.GUILD_ID)
        except Exception as e:
            logging.error(e)

        await sleep(5 * 30)
