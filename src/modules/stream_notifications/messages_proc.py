from enum import StrEnum

from pydantic import BaseModel
from twitchAPI.object.eventsub import ChannelChatMessageEvent

from core.config import config
from .twitch.authorize import authorize


class ChatMessage(BaseModel):
    text: str


class ChatMessageReplyMetadata(BaseModel):
    parent_message_id: str
    parent_message_body: str

    parent_user_id: str
    parent_user_name: str
    parent_user_login: str

    thread_message_id: str

    thread_user_id: str
    thread_user_name: str
    thread_user_login: str


class MessageType(StrEnum):
    TEXT = "text"
    CHANNEL_POINTS_HIGHLIGHTED = "channel_points_highlighted"
    CHANNEL_POINTS_SUB_ONLY = "channel_points_sub_only"
    USER_INTRO = "user_intro"


class MessageEvent(BaseModel):
    broadcaster_user_id: str
    broadcaster_user_name: str
    broadcaster_user_login: str

    chatter_user_id: str
    chatter_user_name: str
    chatter_user_login: str

    message_id: str
    message: ChatMessage
    message_type: MessageType

    color: str
    reply: ChatMessageReplyMetadata | None

    channel_points_custom_reward_id: str

    @classmethod
    def from_twitch_event(cls, event: ChannelChatMessageEvent):
        return cls(
            broadcaster_user_id=event.event.broadcaster_user_id,
            broadcaster_user_name=event.event.broadcaster_user_name,
            broadcaster_user_login=event.event.broadcaster_user_login,

            chatter_user_id=event.event.chatter_user_id,
            chatter_user_name=event.event.chatter_user_name,
            chatter_user_login=event.event.chatter_user_login,

            message_id=event.event.message_id,
            message=ChatMessage(text=event.event.message.text),
            message_type=MessageType(event.event.message_type),

            color=event.event.color,
            reply=ChatMessageReplyMetadata(
                parent_message_id=event.event.reply.parent_message_id,
                parent_message_body=event.event.reply.parent_message_body,

                parent_user_id=event.event.reply.parent_user_id,
                parent_user_name=event.event.reply.parent_user_name,
                parent_user_login=event.event.reply.parent_user_login,

                thread_message_id=event.event.reply.thread_message_id,

                thread_user_id=event.event.reply.thread_user_id,
                thread_user_name=event.event.reply.thread_user_name,
                thread_user_login=event.event.reply.thread_user_login
            ) if event.event.reply else None,

            channel_points_custom_reward_id=event.event.channel_points_custom_reward_id
        )



class MessagesProc:
    @classmethod
    async def on_message(cls, event: MessageEvent):
        if event.message.text == "!hello":
            twitch = await authorize()

            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "Hello, world!"
            )
