from fastapi import APIRouter

from httpx_oauth.oauth2 import OAuth2

from core.config import config


auth_router = APIRouter(prefix="/auth", tags=["auth"])


twitch_oauth = OAuth2(
    config.TWITCH_CLIENT_ID,
    config.TWITCH_CLIENT_SECRET,
    "https://id.twitch.tv/oauth2/authorize",
    "https://id.twitch.tv/oauth2/token",
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
