from core.config import config

from domain.auth import OAuthProvider

from .providers import get_client


REDIRECT_URI_TEMPLATE = f"https://{config.WEB_APP_HOST}/" + "auth/callback/{service}/"


async def get_authorization_url(provider: OAuthProvider) -> str:
    client = get_client(provider)

    return await client.get_authorization_url(
        redirect_uri=REDIRECT_URI_TEMPLATE.format(
            service=provider.value
        ),
    )
