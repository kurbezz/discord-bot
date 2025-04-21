from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from applications.common.repositories.streamers import StreamerConfigRepository
    from applications.schedule_sync.synchronizer import syncronize


class ScheduleSyncActivity:
    @classmethod
    @activity.defn
    async def syncronize(cls, twitch_id: int):
        streamer = await StreamerConfigRepository.get_by_twitch_id(twitch_id)

        if streamer.integrations.discord is None:
            return

        await syncronize(streamer.twitch, streamer.integrations.discord.guild_id)
