import logging
from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.schemas import ForecastRequest, ForecastResponse
from data_interface_service.services.forecast_service import get_history, get_forecast
from data_interface_service.exceptions import ServiceError, AuthorizationError
from shared.db import get_async_session
from shared.models import Hotel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/fetch",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение прогноза и истории бронирований",
    response_description="Возвращает историю и прогноз бронирований по отелю",
    responses={
        200: {"description": "Прогноз успешно получен"},
        400: {"description": "Некорректные входные данные"},
        401: {"description": "Неверный идентификатор отеля"},
        404: {"description": "Данные для прогноза отсутствуют"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def fetch_forecast(
    req: ForecastRequest,
    x_hotel_id: int = Header(..., alias="x-hotel-id"),
    db: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """
    Возвращает историю бронирований и прогноз по заданным параметрам.
    """

    # --- Проверка авторизации отеля ---
    hotel = await db.get(Hotel, x_hotel_id)
    if not hotel:
        raise AuthorizationError()

    try:
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

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ForecastResponse(
                hotel_id=hotel.id,
                history_summary=history_data,
                forecast=forecast_data,
            ).model_dump(),
        )

    except ServiceError as e:
        logger.warning("Ошибка прогноза (hotel_id=%s): %s", x_hotel_id, e.message)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"type": e.__class__.__name__, "message": e.message}}
        )

    except Exception as e:
        logger.exception("Необработанная ошибка при получении прогноза (hotel_id=%s): %s", x_hotel_id, e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"type": "InternalServerError", "message": "Внутренняя ошибка сервера"}},
        )
