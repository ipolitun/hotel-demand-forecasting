import logging
from fastapi import FastAPI, Header, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.db import get_async_session
from shared.db_models import Hotel
from shared.errors import register_error_handlers, setup_openapi_with_errors, AuthorizationError, register_errors
from auth_service.config import auth_config
from auth_service.utils import create_access_token

logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service API")

register_error_handlers(app)
setup_openapi_with_errors(app)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


@app.get("/")
async def root():
    return {"message": "AUTH_SERVICE is running"}


@app.post(
    "/token/system",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Выдача системного токена планировщику",
)
@register_errors(AuthorizationError)
async def generate_system_token(
    x_system_key: str = Header(..., alias="X-System-Key")
):
    """
    Генерация токена для системного планировщика.
    """
    if x_system_key != auth_config.scheduler_key:
        logger.warning("Попытка генерации токена с неверным системным ключом")
        raise AuthorizationError("Invalid system key")

    payload = {"sub": "scheduler", "role": "scheduler"}
    token = create_access_token(payload)

    logger.info("Выдан системный токен планировщику")
    return TokenResponse(access_token=token)


@app.post(
    "/token/user",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Выдача токена для отеля по API-ключу",
)
@register_errors(AuthorizationError)
async def generate_user_token(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Генерация токена для отеля по API-ключу.
    """
    result = await db.execute(select(Hotel).where(Hotel.api_key == x_api_key))
    hotel = result.scalars().first()

    if not hotel:
        logger.warning("Попытка входа с неверным API ключом", extra={"api_key": x_api_key})
        raise AuthorizationError("Invalid API key")

    payload = {"sub": str(hotel.id), "role": "user", "hotel_id": hotel.id}
    token = create_access_token(payload)

    logger.info("Сгенерирован токен для hotel_id=%s", hotel.id)
    return TokenResponse(access_token=token)
