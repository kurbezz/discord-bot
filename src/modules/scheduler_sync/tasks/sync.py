from core.broker import broker
from repositories.streamers import StreamerConfigRepository
from ..synchronizer import syncronize


@broker.task()
async def syncronize_task(twitch_id: int):
    streamer = await StreamerConfigRepository.get_by_twitch_id(twitch_id)

    if streamer.integrations.discord is None:
        return

    await syncronize(streamer.twitch, streamer.integrations.discord.guild_id)


@broker.task(schedule=[{"cron": "*/5 * * * *"}])
async def syncronize_all_task():
    streamers = await StreamerConfigRepository().all()

    for streamer in streamers:
        if streamer.integrations.discord is None:
            continue

        await syncronize_task.kiq(streamer.twitch.id)
