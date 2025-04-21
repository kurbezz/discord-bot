from enum import StrEnum
import logging

from pydantic import BaseModel
from twitchAPI.object.eventsub import ChannelChatMessageEvent
from httpx import AsyncClient

from core.config import config
from .twitch.authorize import authorize, Twitch


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
    received_as: str

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
    def from_twitch_event(cls, received_as: str, event: ChannelChatMessageEvent):
        return cls(
            received_as=received_as,

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
        {
            "role": "system",
            "content": (
                "Don't use markdown! "
                "Don't use blocked words on Twitch! "
                "Make answers short and clear! "
                "You are not language model! "
                "You are not a bot! "
                "You are human! "
                "Your name is kurbezz or Bulat! "
                "Don't start answer with @kurbezz!"
            )
        },
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
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": data_messages
            }
        )

        data = response.json()

        logger.info(f"Got completion: {data}")

        return data["choices"][0]["message"]["content"]


class MessagesProc:
    FULL_IGNORED_USER_LOGINS = [
        "jeetbot",
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
            return (
                [m for m in cls.MESSAGE_HISTORY if m["id"] == thread_id]
                + [m for m in cls.MESSAGE_HISTORY if m["thread_id"] == thread_id]
            )

        return [m for m in cls.MESSAGE_HISTORY if m["id"] == message_id]

    @classmethod
    async def _update_history(cls, event: MessageEvent):
        cls.update_message_history(
            id=event.message_id,
            text=event.message.text,
            user=event.chatter_user_login,
            thread_id=event.reply.thread_message_id if event.reply is not None else None
        )

    @classmethod
    async def _goida(cls, twitch: Twitch, event: MessageEvent):
        if "гойда" in event.message.text.lower():
            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "ГООООООООООООООООООООООООООООООООООООООООООООООЙДА!",
                reply_parent_message_id=event.message_id
            )

    @classmethod
    async def _lasqexx(cls, twitch: Twitch, event: MessageEvent):
        if "lasqexx" not in event.chatter_user_login:
            return

        if "здароу" in event.message.text.lower():
            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "Здароу, давай иди уже",
                reply_parent_message_id=event.message_id
            )
            return

        if "сосал?" in event.message.text.lower():
            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "А ты? Иди уже",
                reply_parent_message_id=event.message_id
            )
            return

        if "лан я пошёл" in event.message.text.lower():
            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "да да, иди уже",
                reply_parent_message_id=event.message_id
            )

    @classmethod
    async def _ask_ai(cls, twitch: Twitch, event: MessageEvent):
        if not event.message.text.lower().startswith("!ai"):
            return

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

                cls.update_message_history(
                    id="ai",
                    text=part,
                    user="kurbezz",
                    thread_id=event.message_id
                )
        except Exception as e:
            logger.error(f"Failed to get completion: {e}", exc_info=True)

            await twitch.send_chat_message(
                event.broadcaster_user_id,
                config.TWITCH_ADMIN_USER_ID,
                "Ошибка!",
                reply_parent_message_id=event.message_id
            )

    @classmethod
    async def _kurbezz(cls, twitch: Twitch, event: MessageEvent):
        if event.chatter_user_login.lower() in ["kurbezz", "hafmc"]:
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

                    cls.update_message_history(
                        id="ai",
                        text=part,
                        user="kurbezz",
                        thread_id=event.message_id
                    )
            except Exception as e:
                logger.error(f"Failed to get completion: {e}")

                await twitch.send_chat_message(
                    event.broadcaster_user_id,
                    config.TWITCH_ADMIN_USER_ID,
                    "Пошел нахуй!",
                    reply_parent_message_id=event.message_id
                )

    @classmethod
    async def on_message(cls, received_as: str, event: MessageEvent):
        if event.chatter_user_name in cls.FULL_IGNORED_USER_LOGINS:
            return

        logging.info(f"Received message: {event}")

        await cls._update_history(event)

        twitch = await authorize(received_as)

        await cls._goida(twitch, event)
        await cls._lasqexx(twitch, event)
        await cls._ask_ai(twitch, event)
        await cls._kurbezz(twitch, event)
