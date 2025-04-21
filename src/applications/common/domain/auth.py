from enum import StrEnum

from pydantic import BaseModel


class OAuthProvider(StrEnum):
    TWITCH = "twitch"


class OAuthData(BaseModel):
    id: str
    email: str | None
