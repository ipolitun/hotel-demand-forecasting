import redis.asyncio as redis
from functools import lru_cache
from auth_service.config import auth_config


class RedisClient:
    def __init__(self):
        self._client: redis.Redis | None = None

    def get_client(self) -> redis.Redis:
        if not self._client:
            self._client = redis.Redis(
                host=auth_config.redis.host,
                port=auth_config.redis.port,
                decode_responses=True
            )
        return self._client


@lru_cache()
def get_redis_client() -> redis.Redis:
    return RedisClient().get_client()
