from fastapi import APIRouter, Depends
from authx import RequestToken

from modules.web_app.auth.authx import auth
from modules.web_app.serializers.streamer import StreamerSerializer
from repositories.streamers import StreamerConfigRepository
from repositories.users import UserRepository
from domain.auth import OAuthProvider


streamer_router = APIRouter(prefix="/api/streamers")


@streamer_router.get("/")
async def get_streamers(
    token: RequestToken = Depends(RequestToken)
) -> list[StreamerSerializer]:
    payload = auth.verify_token(token)

    u_id = payload.sub
    is_admin: bool = getattr(payload, "is_admin", False)


    if is_admin:
        streamers = await StreamerConfigRepository.all()
    else:
        user = await UserRepository.get(u_id)

        twith_oauth = user.oauths.get(OAuthProvider.TWITCH)
        if not twith_oauth:
            return []

        streamers = [await StreamerConfigRepository.get_by_twitch_id(
            int(twith_oauth.id)
        )]

    return [StreamerSerializer(**streamer.model_dump()) for streamer in streamers]
