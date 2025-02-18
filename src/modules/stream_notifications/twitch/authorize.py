from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope

from core.config import config

from .token_storage import TokenStorage


SCOPES = [
    scope for scope in AuthScope
]


async def authorize(auto_refresh_auth: bool = False) -> Twitch:
    twitch = Twitch(
        config.TWITCH_CLIENT_ID,
        config.TWITCH_CLIENT_SECRET
    )

    twitch.user_auth_refresh_callback = TokenStorage.save
    twitch.auto_refresh_auth = auto_refresh_auth

    token, refresh_token = await TokenStorage.get()
    await twitch.set_user_authentication(
        token,
        SCOPES,
        refresh_token=refresh_token if auto_refresh_auth else None
    )

    await twitch.authenticate_app(SCOPES)

    return twitch
