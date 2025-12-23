import httpx
from fastapi import Header, Request, Cookie, Depends

from router.api.schemas import AccessibleHotel
from router.api.utils.jwt import (
    decode_access_jwt,
    validate_base_principal,
    extract_accessible_hotels
)
from shared.errors import AuthorizationError


# === HTTP client dependency ===
async def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Возвращает общий экземпляр httpx.AsyncClient, инициализированный в lifespan.
    """
    return request.app.state.http_client


# === JWT verification ===
def get_access_token(
        access_token: str | None = Cookie(default=None),
) -> str:
    """
    Извлекает access-token из cookie.
    """
    if not access_token:
        raise AuthorizationError("Access token missing")
    return access_token


def get_jwt_principal(
        token: str = Depends(get_access_token),
) -> dict:
    """
    Dependency, используемая роутерами API Gateway.

    Выполняет:
    - извлечение access-token
    - валидацию JWT
    - формирование security-контекста (principal)
    """
    payload = decode_access_jwt(token)

    return validate_base_principal(payload)


def get_current_hotel(
        x_hotel_id: int = Header(..., alias="X-Hotel-Id"),
        payload: dict = Depends(get_jwt_principal),
) -> AccessibleHotel:
    hotels = extract_accessible_hotels(payload)

    for hotel in hotels:
        if hotel.id == x_hotel_id:
            return hotel

    raise AuthorizationError("Access to hotel denied")
