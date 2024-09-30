from typing import Optional
from datetime import datetime
from enum import StrEnum

import icalendar

from httpx import AsyncClient
from pydantic import BaseModel


class Weekday(StrEnum):
    Mon = "MO"
    Tue = "TU"
    Wed = "WE"
    Thu = "TH"
    Fri = "FR"
    Sat = "SA"
    Sun = "SU"

    def get_number(self) -> int:
        return {
            Weekday.Mon: 0,
            Weekday.Tue: 1,
            Weekday.Wed: 2,
            Weekday.Thu: 3,
            Weekday.Fri: 4,
            Weekday.Sat: 5,
            Weekday.Sun: 6
        }[self]


class WeeklyRepeatRule(BaseModel):
    weekday: Weekday


class TwitchEvent(BaseModel):
    uid: str
    start_at: datetime
    end_at: datetime
    name: str
    description: Optional[str]
    categories: Optional[str]
    repeat_rule: Optional[WeeklyRepeatRule]


async def get_twitch_events(twitch_channel_id: str) -> list[TwitchEvent]:
    async with AsyncClient() as client:
        response = await client.get(
            f"https://api.twitch.tv/helix/schedule/icalendar?broadcaster_id={twitch_channel_id}"
        )

        events: list[TwitchEvent] = []

        calendar = icalendar.Calendar.from_ical(response.text)

        for raw_event in calendar.walk("VEVENT"):
            event = TwitchEvent(
                uid=raw_event.get("UID"),
                start_at=raw_event.get("DTSTART").dt,
                end_at=raw_event.get("DTEND").dt,
                name=raw_event.get("SUMMARY"),
                description=raw_event.get("DESCRIPTION"),
                categories=raw_event.get("CATEGORIES").cats[0],
                repeat_rule=None
            )

            if raw_event.get("RRULE"):
                if raw_event.get("RRULE")["FREQ"][0] == "WEEKLY":
                    value = raw_event.get("RRULE")["BYDAY"][0]
                    event.repeat_rule = WeeklyRepeatRule(weekday=Weekday(value))
                else:
                    raise ValueError("Invalid repeat rule")

            if event.start_at > datetime.now(event.start_at.tzinfo) or event.repeat_rule:
                events.append(event)

        return events
