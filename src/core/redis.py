import contextlib

from redis.asyncio import from_url

from core.config import config


def create_redis_pool():
    return from_url(config.REDIS_URI)


class RedisSessionManager:
    def __init__(self):
        self.pool = None

    async def init(self):
        self.pool = await create_redis_pool()

    async def close(self):
        if self.pool is not None:
            await self.pool.close()

    @contextlib.asynccontextmanager
    async def connect(self):
        if self.pool is None:
            await self.init()

        assert self.pool is not None

        yield self.pool


redis_manager = RedisSessionManager()
