import httpx
from typing import Dict
from fastapi import Header, Request
from jose import jwt, JWTError, ExpiredSignatureError

from router.config import router_config
from shared.errors import AuthorizationError


# === HTTP client dependency ===
async def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Возвращает общий экземпляр httpx.AsyncClient, инициализированный в lifespan.
    """
    return request.app.state.http_client


# === JWT verification ===
def verify_token(authorization: str = Header(...)) -> Dict:
    """
    Проверка JWT-токена.
    """
    try:
        scheme, token = authorization.split()
    except ValueError as exc:
        raise AuthorizationError("Некорректный формат заголовка Authorization") from exc

    if scheme.lower() != "bearer":
        raise AuthorizationError("Invalid authentication scheme")

    try:
        payload = jwt.decode(token, router_config.secret_key, algorithms=[router_config.algorithm])
    except ExpiredSignatureError:
        raise AuthorizationError("Token expired")
    except JWTError as exc:
        raise AuthorizationError("Token verification failed") from exc

    if "sub" not in payload or "role" not in payload:
        raise AuthorizationError("Invalid token payload")

    if payload["role"] == "user" and "hotel_id" not in payload:
        raise AuthorizationError("Invalid token payload")

    return payload