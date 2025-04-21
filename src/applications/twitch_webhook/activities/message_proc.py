from temporalio import activity

from applications.twitch_webhook.messages_proc import MessageEvent, MessagesProc


@activity.defn
async def on_message_activity(
    received_as: str,
    event: MessageEvent
):
    await MessagesProc.on_message(received_as, event)
