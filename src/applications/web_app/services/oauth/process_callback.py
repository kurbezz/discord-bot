from domain.auth import OAuthProvider

from .providers import get_client
from .authorization_url_getter import REDIRECT_URI_TEMPLATE


async def process_callback(provider: OAuthProvider, code: str) -> tuple[str, str | None]:
    client = get_client(provider)
    token = await client.get_access_token(
        code,
        redirect_uri=REDIRECT_URI_TEMPLATE.format(service=provider.value),
    )

    user_data = await client.get_id_email(token["access_token"])

    return user_data
