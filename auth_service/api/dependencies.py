import json

from fastapi import Depends, Header, Cookie

from auth_service.repositories.unit_of_work import IUnitOfWork, SQLAlchemyUnitOfWork
from auth_service.schemas.auth import AuthPrincipal, HotelPrincipal
from auth_service.schemas.hotel import HotelAccessPayload
from auth_service.schemas.roles import SystemRole
from auth_service.services.token.jwt_auth import JWTAuthService
from auth_service.services.token.jwt_provider import JWTProvider
from auth_service.services.token.redis_token_storage import RedisTokenStorage

from shared.errors import AuthorizationError


def get_uow() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork()


def get_token_provider() -> JWTProvider:
    return JWTProvider()


def get_token_storage() -> RedisTokenStorage:
    return RedisTokenStorage()


def get_token_auth_service(
        token_provider: JWTProvider = Depends(get_token_provider),
        token_storage: RedisTokenStorage = Depends(get_token_storage)
) -> JWTAuthService:
    return JWTAuthService(
        token_provider=token_provider,
        token_storage=token_storage
    )


def get_principal(
        x_user_id: int = Header(..., alias="X-User-Id"),
) -> AuthPrincipal:
    return AuthPrincipal(user_id=x_user_id)


def get_hotel_principal(
        x_user_id: int = Header(..., alias="X-User-Id"),
        x_system_role: SystemRole = Header(..., alias="X-System-Role"),
        x_hotels: str = Header(..., alias="X-Hotels"),
) -> HotelPrincipal:
    hotels = [
        HotelAccessPayload(**item)
        for item in json.loads(x_hotels)
    ]

    return HotelPrincipal(
        user_id=x_user_id,
        system_role=x_system_role,
        hotels=hotels,
    )


def get_refresh_cookie(
        refresh_token: str | None = Cookie(default=None),
) -> str:
    if not refresh_token:
        raise AuthorizationError("Refresh token missing")
    return refresh_token
