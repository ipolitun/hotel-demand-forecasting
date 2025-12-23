from auth_service.schemas.token import TokenRefreshPayload
from auth_service.services.token.jwt_auth import JWTAuthService

from shared.errors import AuthorizationError


async def logout(
        refresh_token: str,
        auth: JWTAuthService,
) -> None:
    payload = await auth.read_token(refresh_token)

    if not isinstance(payload, TokenRefreshPayload):
        raise AuthorizationError("Invalid refresh token")

    await auth.revoke_token(
        jti=payload.jti,
        user_id=payload.sub,
    )


async def logout_all(
    user_id: int,
    refresh_token: str,
    auth: JWTAuthService,
) -> None:
    payload = await auth.read_token(refresh_token)

    if not isinstance(payload, TokenRefreshPayload):
        raise AuthorizationError("Invalid refresh token")

    if payload.sub != str(user_id):
        raise AuthorizationError("Invalid refresh token")

    await auth.revoke_all_tokens(str(user_id))