from datetime import datetime, timezone

from jose import JWTError

from auth_service.schemas.token import TokenRefreshPayload
from auth_service.redis_client import get_redis_client


class RedisTokenStorage:
    def __init__(self):
        self.redis = get_redis_client()

    async def store_token(self, payload: TokenRefreshPayload) -> None:
        if not payload.jti or not payload.exp:
            raise JWTError("Not valid token")

        ttl_seconds = int(payload.exp - datetime.now(timezone.utc).timestamp())
        await self.redis.setex(self._get_token_key(payload.jti), ttl_seconds, payload.sub)
        await self.redis.sadd(self._get_user_tokens_key(payload.sub), payload.jti)

    async def revoke_token(self, jti: str, user_id: str) -> None:
        await self.redis.delete(self._get_token_key(jti))
        await self.redis.srem(self._get_user_tokens_key(user_id), jti)

    async def revoke_all_tokens(self, user_id: str) -> None:
        tokens_set_key = self._get_user_tokens_key(user_id)
        jti_set = await self.redis.smembers(tokens_set_key)

        for jti in jti_set:
            await self.redis.delete(self._get_token_key(jti))
        await self.redis.delete(tokens_set_key)

    async def is_token_valid(self, jti: str) -> bool:
        return await self.redis.exists(self._get_token_key(jti)) == 1

    @staticmethod
    def _get_token_key(jti: str) -> str:
        return f"refresh_token:{jti}"

    @staticmethod
    def _get_user_tokens_key(user_id: str) -> str:
        return f"user_refresh_tokens:{user_id}"
