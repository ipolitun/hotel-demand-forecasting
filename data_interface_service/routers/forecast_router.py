import logging
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.schemas import ForecastRequest, ForecastResponse
from data_interface_service.services.forecast_service import get_history, get_forecast
from shared.db import get_async_session
from shared.db_models import Hotel
from shared.errors import (
    AuthorizationError,
    NoForecastError,
    InsufficientHistoryError,
    DatabaseError,
    register_errors,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/fetch",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение истории и прогноза бронирований",
    response_description="Возвращает историю и прогноз по заданным параметрам.",
)
@register_errors(
    AuthorizationError, NoForecastError,
    InsufficientHistoryError, DatabaseError
)
async def fetch_forecast(
    req: ForecastRequest,
    x_hotel_id: int = Header(..., alias="x-hotel-id"),
    db: AsyncSession = Depends(get_async_session),
) -> ForecastResponse:
    """
    Возвращает историю бронирований и прогноз по заданным параметрам.
    """

    hotel = await db.get(Hotel, x_hotel_id)
    if not hotel:
        raise AuthorizationError()

    history_data = await get_history(
        db=db,
        hotel_id=hotel.id,
        target_date=req.target_date,
        has_deposit=req.has_deposit,
        history_window=req.history_window,
    )

    forecast_data = await get_forecast(
        db=db,
        hotel_id=hotel.id,
        target_date=req.target_date,
        has_deposit=req.has_deposit,
        horizon=req.horizon,
    )

    logger.info(
        "Прогноз успешно получен: hotel_id=%s, history=%s, forecast=%s",
        hotel.id, len(history_data), len(forecast_data)
    )

    return ForecastResponse(
        hotel_id=hotel.id,
        history_summary=history_data,
        forecast=forecast_data,
    )