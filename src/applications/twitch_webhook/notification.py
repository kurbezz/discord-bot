import logging

from httpx import AsyncClient

from core.config import config
from applications.common.domain.streamers import StreamerConfig

from .state import State
from .sent_notifications import SentNotification, SentNotificationType, SentResult


logger = logging.getLogger(__name__)


async def notify_telegram(msg: str, chat_id: str) -> SentResult:
    async with AsyncClient() as client:
        try:
            result = await client.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": msg,
                }
            )

            result.raise_for_status()
        except Exception as e:
            logger.error("Failed to notify telegram", exc_info=e)
            return SentResult(success=False, message_id=None)

        if result.json()["ok"] is False:
            return SentResult(success=False, message_id=None)

        return SentResult(success=True, message_id=str(result.json()["result"]["message_id"]))


async def delete_telegram_message(chat_id: int, message_id: int):
    async with AsyncClient() as client:
        try:
            result = await client.post(
                f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/deleteMessage",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id
                }
            )

            if result.status_code != 200:
                return False
        except Exception as e:
            logger.error("Failed to delete telegram message", exc_info=e)
            return False

        return True


async def notify_discord(msg: str, channel_id: str) -> SentResult:
    async with AsyncClient() as client:
        try:
            result = await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"
                },
                json={
                    "content": msg,
                }
            )

            result.raise_for_status()
        except Exception as e:
            logger.error("Failed to notify discord", exc_info=e)
            return SentResult(success=False, message_id=None)

        return SentResult(success=True, message_id=result.json()["id"])


def get_role_id(streamer_config: StreamerConfig, category: str) -> int | None:
    discord_integration = streamer_config.integrations.discord
    if discord_integration is None:
        return None

    roles= discord_integration.roles
    if roles is None:
        return None

    return roles.get(category)


async def notify(notification_type: SentNotificationType, streamer_config: StreamerConfig, current_state: State) -> dict[str, SentResult]:
    result: dict[str, SentResult] = {}

    if notification_type == SentNotificationType.START_STREAM:
        message_template = streamer_config.notifications.start_stream
    else:
        message_template = streamer_config.notifications.change_category

    if message_template is None:
        return result

    integrations = streamer_config.integrations

    if (telegram := integrations.telegram) is not None:
        if telegram.notifications_channel_id is not None:
            msg = message_template.format(
                title=current_state.title,
                category=current_state.category,
                role=""
            )

            result["telegram"] = await notify_telegram(msg, str(telegram.notifications_channel_id))

    if (discord := integrations.discord) is not None:
        if discord.notifications_channel_id is not None:
            # TODO: Get roles from discord api

            role_id = get_role_id(streamer_config, current_state.category)
            if role_id is not None:
                role = f"<@&{role_id}>"
            else:
                role = ""

            msg = message_template.format(
                title=current_state.title,
                category=current_state.category,
                role=role
            )

            result["discord"] = await notify_discord(msg, str(discord.notifications_channel_id))

    return result


async def delete_penultimate_notification(streamer_config: StreamerConfig, sent_notification: SentNotification):
    telegram_config = streamer_config.integrations.telegram
    telegram_data = sent_notification.sent_result.get("telegram")

    if telegram_data and telegram_data.message_id and telegram_config:
        await delete_telegram_message(telegram_config.notifications_channel_id, int(telegram_data.message_id))
