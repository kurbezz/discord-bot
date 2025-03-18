from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope

from core.config import config

from .token_storage import TokenStorage


SCOPES = [
    AuthScope.CHAT_READ,

    AuthScope.CHANNEL_BOT,

    AuthScope.USER_BOT,
    AuthScope.USER_READ_CHAT,
    AuthScope.USER_WRITE_CHAT,

    AuthScope.CHANNEL_READ_REDEMPTIONS,
]


async def authorize(user: str, auto_refresh_auth: bool = False) -> Twitch:
    twitch = Twitch(
        config.TWITCH_CLIENT_ID,
        config.TWITCH_CLIENT_SECRET
    )

    twitch.user_auth_refresh_callback = lambda a, r: TokenStorage.save(user, a, r)
    twitch.auto_refresh_auth = auto_refresh_auth

    token, refresh_token = await TokenStorage.get(user)
    await twitch.set_user_authentication(
        token,
        SCOPES,
        refresh_token=refresh_token if auto_refresh_auth else None
    )

    await twitch.authenticate_app(SCOPES)

    return twitch
