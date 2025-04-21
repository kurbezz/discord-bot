from httpx_oauth.oauth2 import OAuth2

from domain.auth import OAuthProvider
from .twitch import twitch_oauth_client


def get_client(provider: OAuthProvider) -> OAuth2:
    if provider == OAuthProvider.TWITCH:
        return twitch_oauth_client
    else:
        raise NotImplementedError("Provider is not implemented")
