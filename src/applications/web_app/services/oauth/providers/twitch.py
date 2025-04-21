from twitchAPI.twitch import Twitch, AuthScope
from twitchAPI.helper import first

from httpx_oauth.oauth2 import OAuth2

from core.config import config


class TwithOAuth2(OAuth2):
    async def get_id_email(self, token: str):
        twitch_client = Twitch(config.TWITCH_CLIENT_ID, config.TWITCH_CLIENT_SECRET)
        twitch_client.auto_refresh_auth = False

        await twitch_client.set_user_authentication(
            token,
            [AuthScope.USER_READ_EMAIL],
            validate=True
        )

        me = await first(twitch_client.get_users())

        if me is None:
            raise Exception("Failed to get user data")

        return me.id, me.email


twitch_oauth_client = TwithOAuth2(
    config.TWITCH_CLIENT_ID,
    config.TWITCH_CLIENT_SECRET,
    "https://id.twitch.tv/oauth2/authorize",
    "https://id.twitch.tv/oauth2/token",
    base_scopes=[AuthScope.USER_READ_EMAIL.value],
)
