import logging
from typing import Literal

from httpx import AsyncClient

from core.config import config, StreamerConfig

from .twitch.state import State


logger = logging.getLogger(__name__)


async def notify_telegram(msg: str, chat_id: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": msg,
            }
        )


async def notify_discord(msg: str, channel_id: str):
    async with AsyncClient() as client:
        await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"
            },
            json={
                "content": msg,
            }
        )


def get_role_id(streamer_config: StreamerConfig, category: str) -> int | None:
    discord_integration = streamer_config.integrations.discord
    if discord_integration is None:
        return None

    roles= discord_integration.roles
    if roles is None:
        return None

    return roles.get(category)


async def notify(notification_type: Literal["start"] | Literal["change_category"], streamer_config: StreamerConfig, current_state: State):
    if notification_type == "start":
        message_template = streamer_config.notifications.start_stream
    else:
        message_template = streamer_config.notifications.change_category

    if message_template is None:
        return

    integrations = streamer_config.integrations

    if (telegram := integrations.telegram) is not None:
        if telegram.notifications_channel_id is not None:
            msg = message_template.format(
                title=current_state.title,
                category=current_state.category,
                role=""
            )

            try:
                await notify_telegram(msg, str(telegram.notifications_channel_id))
            except Exception as e:
                logger.error("Failed to notify telegram", exc_info=e)

    if (discord := integrations.discord) is not None:
        if discord.notifications_channel_id is not None:
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

            try:
                await notify_discord(msg, str(discord.notifications_channel_id))
            except Exception as e:
                logger.error("Failed to notify discord", exc_info=e)
