from fastapi import APIRouter

from domain.auth import OAuthProvider, OAuthData
from domain.users import CreateUser
from modules.web_app.services.oauth.process_callback import process_callback
from modules.web_app.services.oauth.authorization_url_getter import get_authorization_url as gen_auth_link
from modules.web_app.serializers.auth import GetAuthorizationUrlResponse, CallbackResponse
from modules.web_app.auth.authx import auth
from repositories.users import UserRepository


auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.get("/get_authorization_url/{provider}/")
async def get_authorization_url(provider: OAuthProvider) -> GetAuthorizationUrlResponse:
    link = await gen_auth_link(provider)

    return GetAuthorizationUrlResponse(authorization_url=link)


@auth_router.get("/callback/{provider}/")
async def callback(provider: OAuthProvider, code: str) -> CallbackResponse:
    user_data = await process_callback(provider, code)

    user = await UserRepository.get_or_create_user(
        CreateUser(
            oauths={provider: OAuthData(id=user_data[0], email=user_data[1])},
            is_admin=False,
        )
    )

    token = auth.create_access_token(
        uid=user.id,
        is_admin=user.is_admin
    )

    return CallbackResponse(token=token)
