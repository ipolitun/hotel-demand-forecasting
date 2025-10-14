import httpx
from typing import Dict
from fastapi import Header, HTTPException, Request
from jose import jwt, JWTError

from router.config import SECRET_KEY, ALGORITHM


# --- HTTP client dependency ---
async def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Возвращает общий экземпляр httpx.AsyncClient, инициализированный в lifespan.
    """
    return request.app.state.http_client


# --- JWT verification ---
def verify_token(authorization: str = Header(...)) -> Dict:
    """
    Проверка JWT-токена.
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if "sub" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        if payload["role"] == "user" and "hotel_id" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return payload
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token verification failed")
