from temporalio import activity

from applications.common.repositories.streamers import StreamerConfigRepository
from applications.schedule_sync.synchronizer import syncronize as syncronize_internal


@activity.defn
async def syncronize(twitch_id: int):
    streamer = await StreamerConfigRepository.get_by_twitch_id(twitch_id)

    if streamer.integrations.discord is None:
        return

    try:
        await syncronize_internal(streamer.twitch, streamer.integrations.discord.guild_id)
    except Exception as e:
        activity.logger.error(f"Error during synchronization: {e}")
        raise e
