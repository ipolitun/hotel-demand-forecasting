from jose import jwt, JWTError

from router.api.schemas import AccessibleHotel
from router.config import router_config
from shared.errors import AuthorizationError


def decode_access_jwt(token: str) -> dict:
    """
    Декодирует и криптографически проверяет access JWT.

    Проверяет подпись и срок действия токена.
    """
    try:
        return jwt.decode(
            token,
            router_config.jwt_config.secret_key,
            algorithms=[router_config.jwt_config.hash_algorithm],
        )
    except JWTError as exc:
        raise AuthorizationError("Invalid access token") from exc


def validate_base_principal(payload: dict) -> dict:
    """
    Валидирует минимальный security-контракт access JWT.

    Проверяет наличие обязательных claims и тип токена.
    """
    if "sub" not in payload or "system_role" not in payload:
        raise AuthorizationError("Invalid token payload")

    if payload.get("token_type") != "access":
        raise AuthorizationError("Invalid token type")

    return payload


def extract_accessible_hotels(payload: dict) -> list[AccessibleHotel]:
    raw_hotels = payload.get("hotels")

    if not isinstance(raw_hotels, list):
        raise AuthorizationError("Invalid hotels claim")

    try:
        return [AccessibleHotel(**hotel) for hotel in raw_hotels]
    except Exception as exc:
        raise AuthorizationError("Invalid hotels payload") from exc
