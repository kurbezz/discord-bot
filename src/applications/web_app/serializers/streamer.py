from pydantic import BaseModel


class TwitchSerializer(BaseModel):
    id: int
    name: str


class StreamerSerializer(BaseModel):
    twitch: TwitchSerializer
