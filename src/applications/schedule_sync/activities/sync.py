from temporalio import activity

from applications.common.repositories.streamers import StreamerConfigRepository
from applications.schedule_sync.synchronizer import syncronize


class ScheduleSyncActivity:
    @activity.defn
    @classmethod
    async def syncronize(cls, twitch_id: int):
        streamer = await StreamerConfigRepository.get_by_twitch_id(twitch_id)

        if streamer.integrations.discord is None:
            return

        await syncronize(streamer.twitch, streamer.integrations.discord.guild_id)
