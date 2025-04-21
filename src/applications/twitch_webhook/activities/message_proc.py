from temporalio import activity

from applications.twitch_webhook.messages_proc import MessageEvent, MessagesProc


@activity.defn
async def on_message_activity(
    event: MessageEvent
):
    await MessagesProc.on_message(
        event.received_as,
        event
    )
