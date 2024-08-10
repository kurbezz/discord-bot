from datetime import datetime

from services.scheduler_sync.discord_events import DiscordEvent, CreateDiscordEvent, RecurrenceRule


def is_repeated(start: datetime, target: datetime, rule: RecurrenceRule) -> bool:
    return start.time() == target.time() and target.weekday() in rule.by_weekday


def compare(create_event: CreateDiscordEvent, event: DiscordEvent) -> bool:
    if create_event.name != event.name:
        return False

    if create_event.description != event.description:
        return False

    if create_event.recurrence_rule is not None:
        if event.recurrence_rule is None:
            return False

        ce_rr = create_event.recurrence_rule
        e_rr = event.recurrence_rule

        if ce_rr.by_weekday != e_rr.by_weekday:
            return False
        if ce_rr.interval != e_rr.interval:
            return False
        if ce_rr.frequency != e_rr.frequency:
            return False
        if not is_repeated(ce_rr.start, e_rr.start, ce_rr):
            return False
    else:
        if event.recurrence_rule is not None:
            return False

    if create_event.scheduled_start_time != event.scheduled_start_time:
        if create_event.recurrence_rule is None or not is_repeated(create_event.scheduled_start_time, event.scheduled_start_time, create_event.recurrence_rule):
            return False

    if create_event.scheduled_end_time != event.scheduled_end_time:
        if create_event.recurrence_rule is None or not is_repeated(create_event.scheduled_end_time, event.scheduled_end_time, create_event.recurrence_rule):
            return False

    return True
