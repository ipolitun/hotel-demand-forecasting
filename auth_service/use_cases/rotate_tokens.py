from auth_service.repositories.unit_of_work import IUnitOfWork
from auth_service.schemas.auth import HotelPrincipal
from auth_service.schemas.token import TokenRefreshPayload
from auth_service.services.token.jwt_auth import JWTAuthService
from auth_service.use_cases._helpers import get_hotels_payload

from shared.errors import AuthorizationError


async def rotate_tokens(
        refresh_token: str,
        uow: IUnitOfWork,
        auth: JWTAuthService,
) -> tuple[str, str]:
    payload = await auth.read_token(refresh_token)
    if not isinstance(payload, TokenRefreshPayload):
        raise AuthorizationError("Invalid refresh token")

    user_id = int(payload.sub)

    async with uow:
        user = await uow.users.get_by_id(user_id)
        if not user:
            raise AuthorizationError("User not found")

        hotels = await get_hotels_payload(uow=uow, user_id=user_id)

        principal = HotelPrincipal(
            user_id=user_id,
            system_role=user.system_role,
            hotels=hotels,
        )

    access, refresh = await auth.rotate_tokens(
        refresh_payload=payload,
        principal=principal,
    )
    return access, refresh
