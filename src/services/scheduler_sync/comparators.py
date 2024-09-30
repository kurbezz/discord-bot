from datetime import datetime
import logging

from services.scheduler_sync.discord_events import DiscordEvent, CreateDiscordEvent, RecurrenceRule


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def is_repeated(start: datetime, target: datetime, rule: RecurrenceRule) -> bool:
    start_utc = start.astimezone(datetime.now().astimezone().tzinfo)
    target_utc = target.astimezone(datetime.now().astimezone().tzinfo)

    return start_utc.time() == target_utc.time() and target.weekday() in rule.by_weekday


def compare(create_event: CreateDiscordEvent, event: DiscordEvent) -> bool:
    if create_event.name != event.name:
        logger.debug(f"Name is different: {create_event.name} != {event.name}")
        return False

    if create_event.description != event.description:
        logger.debug(f"Description is different: {create_event.description} != {event.description}")
        return False

    if create_event.recurrence_rule is not None:
        if event.recurrence_rule is None:
            logger.debug(f"Recurrence rule is different: {create_event.recurrence_rule} != {event.recurrence_rule}")
            return False

        ce_rr = create_event.recurrence_rule
        e_rr = event.recurrence_rule

        if ce_rr.by_weekday != e_rr.by_weekday:
            logger.debug(f"Recurrence rule is different: {ce_rr.by_weekday} != {e_rr.by_weekday}")
            return False
        if ce_rr.interval != e_rr.interval:
            logger.debug(f"Recurrence rule is different: {ce_rr.interval} != {e_rr.interval}")
            return False
        if ce_rr.frequency != e_rr.frequency:
            logger.debug(f"Recurrence rule is different: {ce_rr.frequency} != {e_rr.frequency}")
            return False
        if not is_repeated(ce_rr.start, e_rr.start, ce_rr):
            logger.debug(f"Recurrence rule is different: {ce_rr.start} != {e_rr.start}")
            return False
    else:
        if event.recurrence_rule is not None:
            logger.debug(f"Recurrence rule is different: {create_event.recurrence_rule} != {event.recurrence_rule}")
            return False

    if create_event.scheduled_start_time != event.scheduled_start_time:
        if create_event.recurrence_rule is None or not is_repeated(create_event.scheduled_start_time, event.scheduled_start_time, create_event.recurrence_rule):
            logger.debug(f"Scheduled start time is different: {create_event.scheduled_start_time} != {event.scheduled_start_time}")
            return False

    if create_event.scheduled_end_time != event.scheduled_end_time:
        if create_event.recurrence_rule is None or not is_repeated(create_event.scheduled_end_time, event.scheduled_end_time, create_event.recurrence_rule):
            logger.debug(f"Scheduled end time is different: {create_event.scheduled_end_time} != {event.scheduled_end_time}")
            return False

    return True
