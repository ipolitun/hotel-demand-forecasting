import logging
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.db import get_async_session
from shared.models import Hotel
from auth_service.config import SCHEDULER_KEY
from auth_service.utils import create_access_token

logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service API")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/")
async def root():
    return {"message": "AUTH_SERVICE работает!"}


@app.post("/token/system", response_model=TokenResponse)
async def generate_system_token(
    x_system_key: str = Header(..., alias="X-System-Key")
):
    """
    Генерация токена для системного планировщика.
    """
    if x_system_key != SCHEDULER_KEY:
        logger.warning("Неверный системный ключ")
        raise HTTPException(status_code=401, detail="Invalid system key")

    payload = {"sub": "scheduler", "role": "scheduler"}
    token = create_access_token(payload)
    return TokenResponse(access_token=token)


@app.post("/token/user", response_model=TokenResponse)
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
        logger.warning("Попытка входа с неверным API ключом: %s", x_api_key)
        raise HTTPException(status_code=401, detail="Invalid API key")

    payload = {"sub": str(hotel.id), "role": "user", "hotel_id": hotel.id}
    token = create_access_token(payload)

    logger.info("Сгенерирован токен для hotel_id=%s", hotel.id)
    return TokenResponse(access_token=token)
