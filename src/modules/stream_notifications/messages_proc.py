from enum import StrEnum
import logging

from pydantic import BaseModel
from twitchAPI.object.eventsub import ChannelChatMessageEvent
from httpx import AsyncClient

from core.config import config
from .twitch.authorize import authorize


logger = logging.getLogger(__name__)


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

    channel_points_custom_reward_id: str | None

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



async def get_completion(messages: list[dict]) -> str:
    logger.info(f"Getting completion for message: {messages}")

    data_messages = [
        # {
        #     "role": "system",
        #     "content": "Don't use markdown! Don't use blocked words on Twitch! Make answers short and clear!"
        # },
        *(
            {
                "role": "assistant" if message["user"] == "kurbezz" else "user",
                "content": message["text"]
            }
            for message in messages
        ),
    ]

    async with AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "content-type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-thinking-exp:free",
                "messages": data_messages
            }
        )

        data = response.json()

        logger.info(f"Got completion: {data}")

        return data["choices"][0]["message"]["content"]


class MessagesProc:
    IGNORED_USER_LOGINS = [
        "jeetbot",
        "kurbezz",
    ]

    MESSAGE_LIMIT = 1000
    MESSAGE_HISTORY = []

    @classmethod
    def update_message_history(cls, id: str, text: str, user: str, thread_id: str | None = None):
        cls.MESSAGE_HISTORY.append({
            "id": id,
            "text": text,
            "user": user,
            "thread_id": thread_id
        })

        if len(cls.MESSAGE_HISTORY) > cls.MESSAGE_LIMIT:
            cls.MESSAGE_HISTORY = cls.MESSAGE_HISTORY[-cls.MESSAGE_LIMIT:]

    @classmethod
    def get_message_history_with_thread(cls, message_id: str, thread_id: str | None = None) -> list[dict]:
        logger.info(f"HISTORY: {cls.MESSAGE_HISTORY}")

        if thread_id is not None:
            thread_messages = [m for m in cls.MESSAGE_HISTORY if m["thread_id"] == thread_id]
        else:
            thread_messages = []

        return thread_messages + [m for m in cls.MESSAGE_HISTORY if m["id"] == message_id]

    @classmethod
    async def on_message(cls, event: MessageEvent):
        logging.info(f"Received message: {event}")

        cls.update_message_history(
            id=event.message_id,
            text=event.message.text,
            user=event.chatter_user_login,
            thread_id=event.reply.thread_message_id if event.reply is not None else None
        )

        if event.chatter_user_name == "pahangor":
            return

        twitch = await authorize()

        if "гойда" in event.message.text.lower():
            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "ГООООООООООООООООООООООООООООООООООООООООООООООЙДА!",
                reply_parent_message_id=event.message_id
            )

        if "lasqexx" in event.chatter_user_login:
            pass  # Todo: Здароу

        if event.message.text.lower().startswith("!ai"):
            try:
                messages = cls.get_message_history_with_thread(
                    event.message_id,
                    thread_id=event.reply.thread_message_id if event.reply is not None else None
                )
                completion = await get_completion(messages)

                max_length = 255
                completion_parts = [completion[i:i + max_length] for i in range(0, len(completion), max_length)]

                for part in completion_parts:
                    await twitch.send_chat_message(
                        event.broadcaster_user_id,
                        config.TWITCH_ADMIN_USER_ID,
                        part,
                        reply_parent_message_id=event.message_id
                    )
            except Exception as e:
                logger.error("Failed to get completion: {}", e, exc_info=True)

                await twitch.send_chat_message(
                    event.broadcaster_user_id,
                    config.TWITCH_ADMIN_USER_ID,
                    "Ошибка!",
                    reply_parent_message_id=event.message_id
                )

        if event.chatter_user_login in cls.IGNORED_USER_LOGINS:
            return

        if ("kurbezz" in event.message.text.lower() or \
            "курбез" in event.message.text.lower() or \
            "булат" in event.message.text.lower()):

            try:
                messages = cls.get_message_history_with_thread(
                    event.message_id,
                    thread_id=event.reply.thread_message_id if event.reply is not None else None
                )
                completion = await get_completion(messages)

                max_length = 255
                completion_parts = [completion[i:i + max_length] for i in range(0, len(completion), max_length)]

                for part in completion_parts:
                    await twitch.send_chat_message(
                        event.broadcaster_user_id,
                        config.TWITCH_ADMIN_USER_ID,
                        part,
                        reply_parent_message_id=event.message_id
                    )
            except Exception as e:
                logger.error(f"Failed to get completion: {e}")

                await twitch.send_chat_message(
                    event.broadcaster_user_id,
                    config.TWITCH_ADMIN_USER_ID,
                    "Пошел нахуй!",
                    reply_parent_message_id=event.message_id
                )
