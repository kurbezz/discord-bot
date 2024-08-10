from asyncio import sleep

from services.scheduler_sync.twitch_events import get_twitch_events, TwitchEvent
from services.scheduler_sync.discord_events import (
    get_discord_events, DiscordEvent,
    delete_discord_event,
    create_discord_event, CreateDiscordEvent,
    edit_discord_event, UpdateDiscordEvent
)
from services.scheduler_sync.comparators import compare


async def add_events(
    twitch_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    discord_events_ids = [event[0] for event in discord_events]

    for (uid, event) in twitch_events:
        if uid not in discord_events_ids:
            create_event = CreateDiscordEvent.parse_from_twitch_event(event)
            await create_discord_event(create_event)


async def remove_events(
    twith_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    twith_events_ids = [event[0] for event in twith_events]

    for (uid, event) in discord_events:
        if uid not in twith_events_ids:
            await delete_discord_event(uid)


async def edit_events(
    twith_events: list[tuple[str, TwitchEvent]],
    discord_events: list[tuple[str, DiscordEvent]]
):
    for (uid, twitch_event) in twith_events:
        for (discord_id, discord_event) in discord_events:
            if uid != discord_id:
                continue

            create_event = CreateDiscordEvent.parse_from_twitch_event(twitch_event)

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

            await edit_discord_event(discord_event.id, update_event)


async def syncronize():
    twitch_events = await get_twitch_events()
    discord_events = await get_discord_events()

    twitch_events_with_id = [(event.uid, event) for event in twitch_events]
    discord_events_with_id = [
        (event.description.rsplit("#")[1], event)
        for event in discord_events
    ]

    await add_events(twitch_events_with_id, discord_events_with_id)
    await remove_events(twitch_events_with_id, discord_events_with_id)
    await edit_events(twitch_events_with_id, discord_events_with_id)


async def start_synchronizer():
    while True:
        try:
            await syncronize()
        except Exception as e:
            print(f"Error: {e}")

        await sleep(5 * 30)
