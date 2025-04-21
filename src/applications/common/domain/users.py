from pydantic import BaseModel

from domain.auth import OAuthProvider, OAuthData


class User(BaseModel):
    id: str

    oauths: dict[OAuthProvider, OAuthData]

    is_admin: bool


class CreateUser(BaseModel):
    oauths: dict[OAuthProvider, OAuthData]

    is_admin: bool = False
