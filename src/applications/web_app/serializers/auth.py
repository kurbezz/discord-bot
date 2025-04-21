from pydantic import BaseModel


class GetAuthorizationUrlResponse(BaseModel):
    authorization_url: str


class CallbackResponse(BaseModel):
    token: str
