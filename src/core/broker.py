from taskiq import TaskiqScheduler
from taskiq.middlewares.retry_middleware import SimpleRetryMiddleware
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from core.config import config


broker = ListQueueBroker(url=config.REDIS_URI) \
    .with_middlewares(
        SimpleRetryMiddleware(default_retry_count=5)
    ) \
    .with_result_backend(RedisAsyncResultBackend(
        redis_url=config.REDIS_URI,
        result_ex_time=60 * 60 * 24 * 7,
    ))


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
