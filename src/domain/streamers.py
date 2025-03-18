from pydantic import BaseModel

class TwitchConfig(BaseModel):
    id: int
    name: str

class NotificationsConfig(BaseModel):
    start_stream: str
    change_category: str | None = None
    redemption_reward: str | None = None

class GamesListConfig(BaseModel):
    channel_id: int
    message_id: int

class DiscordConfig(BaseModel):
    guild_id: int
    notifications_channel_id: int
    games_list: GamesListConfig | None = None
    roles: dict[str, int] | None = None

class TelegramConfig(BaseModel):
    notifications_channel_id: int

class IntegrationsConfig(BaseModel):
    discord: DiscordConfig | None = None
    telegram: TelegramConfig | None = None

class StreamerConfig(BaseModel):
    twitch: TwitchConfig
    notifications: NotificationsConfig
    integrations: IntegrationsConfig
