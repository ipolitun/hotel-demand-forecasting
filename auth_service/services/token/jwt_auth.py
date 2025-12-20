from auth_service.schemas.token import (
    TokenAccessPayload,
    TokenRefreshPayload,
    TokenType,
)
from auth_service.services.token.jwt_provider import JWTProvider
from auth_service.services.token.redis_token_storage import RedisTokenStorage
from auth_service.schemas.auth import HotelPrincipal

from shared.errors import AuthorizationError


class JWTAuthService:
    def __init__(
            self,
            token_provider: JWTProvider,
            token_storage: RedisTokenStorage,
    ):
        self._token_provider = token_provider
        self._token_storage = token_storage

    async def generate_tokens(
            self,
            principal: HotelPrincipal,
    ) -> tuple[str, str]:
        access = self._token_provider.create_access_token(TokenAccessPayload(
            sub=str(principal.user_id),
            token_type=TokenType.ACCESS.value,
            system_role=principal.system_role.value,
            hotels=principal.hotels,
        ))

        refresh = self._token_provider.create_refresh_token(TokenRefreshPayload(
            sub=str(principal.user_id),
            token_type=TokenType.REFRESH
        ))
        refresh_data = await self.read_token(refresh)

        await self._token_storage.store_token(refresh_data)
        return access, refresh

    async def rotate_tokens(
            self,
            refresh_payload: TokenRefreshPayload,
            principal: HotelPrincipal,
    ) -> tuple[str, str]:
        await self._validate_refresh_token(refresh_payload)

        await self.revoke_token(refresh_payload.jti, refresh_payload.sub)
        return await self.generate_tokens(principal)

    async def revoke_token(self, jti: str, user_id: str) -> None:
        await self._token_storage.revoke_token(jti, user_id)

    async def revoke_all_tokens(self, user_id: str) -> None:
        await self._token_storage.revoke_all_tokens(user_id)

    async def read_token(self, token: str) -> TokenAccessPayload | TokenRefreshPayload:
        payload = self._token_provider.decode_token(token)
        if not payload or not isinstance(payload, (TokenAccessPayload, TokenRefreshPayload)):
            raise AuthorizationError("Token decoding failed or unsupported format")
        return payload

    async def _validate_refresh_token(self, payload: TokenRefreshPayload) -> None:
        if not payload.jti:
            raise AuthorizationError("Token missing unique identifier (jti)")

        if not await self._token_storage.is_token_valid(payload.jti):
            raise AuthorizationError("Refresh token is revoked or expired")
