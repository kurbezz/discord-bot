from fastapi import APIRouter

from twitchAPI.twitch import Twitch, AuthScope
from twitchAPI.helper import first
from httpx_oauth.oauth2 import OAuth2

from core.config import config


auth_router = APIRouter(prefix="/auth", tags=["auth"])


class TwithOAuth2(OAuth2):
    async def get_id_email(self, token: str):
        twitch_client = Twitch(config.TWITCH_CLIENT_ID, config.TWITCH_CLIENT_SECRET)
        twitch_client.auto_refresh_auth = False

        await twitch_client.set_user_authentication(
            token,
            [AuthScope.USER_READ_EMAIL],
            validate=False
        )

        me = await first(twitch_client.get_users())

        if me is None:
            raise Exception("Failed to get user data")

        return me.id, me.email


twitch_oauth = TwithOAuth2(
    config.TWITCH_CLIENT_ID,
    config.TWITCH_CLIENT_SECRET,
    "https://id.twitch.tv/oauth2/authorize",
    "https://id.twitch.tv/oauth2/token",
    base_scopes=[AuthScope.USER_READ_EMAIL.value],
)


REDIRECT_URI_TEMPLATE = f"https://{config.WEB_APP_HOST}/" + "auth/callback/{service}/"


@auth_router.get("/get_authorization_url/{service}/")
async def get_authorization_url(service: str):
    link = None

    if service == "twitch":
        link = await twitch_oauth.get_authorization_url(
            redirect_uri=REDIRECT_URI_TEMPLATE.format(service="twitch"),
        )

    return {"link": link}


@auth_router.get("/callback/{service}/")
async def callback(service: str, code: str):
    user_data = None

    if service == "twitch":
        token = await twitch_oauth.get_access_token(
            code,
            redirect_uri=REDIRECT_URI_TEMPLATE.format(service="twitch"),
        )

        user_data = await twitch_oauth.get_id_email(token["access_token"])

    return {"user_data": user_data}
