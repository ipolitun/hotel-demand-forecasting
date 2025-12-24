import logging

import httpx
from fastapi import APIRouter, Depends, UploadFile, File, status, Response

from router.api.dependencies import (
    get_http_client,
    get_current_hotel
)
from router.api.schemas import (
    ForecastRequest,
    ForecastResponse,
    BookingImportResponse,
    AccessibleHotel
)
from router.api.utils.http import forward_response
from router.api.utils.http import proxy_post
from router.config import router_config
from shared.errors import (
    register_errors,
    AuthorizationError,
    ExternalServiceError,
    NoForecastError,
    InsufficientHistoryError,
    DatabaseError,
    MappingError,
    CSVProcessingError,
    ConflictError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/import-bookings",
    response_model=BookingImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Импорт бронирований в систему",
)
@register_errors(
    AuthorizationError, MappingError, CSVProcessingError,
    ConflictError, DatabaseError, ExternalServiceError
)
async def import_bookings(
        response: Response,
        file: UploadFile = File(...),
        hotel: AccessibleHotel = Depends(get_current_hotel),
        client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос для загрузки бронирований.
    Отправляет CSV-файл в `data_interface_service/booking/import`.
    """

    file_content = await file.read()
    files = {"file": (file.filename, file_content, file.content_type)}

    import_response = await proxy_post(
        client=client,
        url=f"{router_config.data_interface_service_url}/booking/import",
        headers={"X-Hotel-Id": str(hotel.id)},
        files=files,
    )
    forward_response(source=import_response, target=response)

    logger.info(
        "Импорт завершён через router_service: hotel_id=%s",
        hotel.id,
    )
    return response


@router.post(
    "/fetch-forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение прогноза из системы",
)
@register_errors(
    AuthorizationError, NoForecastError,
    InsufficientHistoryError, DatabaseError, ExternalServiceError
)
async def fetch_forecast(
        req: ForecastRequest,
        response: Response,
        hotel: AccessibleHotel = Depends(get_current_hotel),
        client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос для получения прогноза.
    Перенаправляет вызов в `data_interface_service/forecast/fetch`.
    """
    headers = {"X-Hotel-Id": str(hotel.id)}

    forecast_response = await proxy_post(
        client=client,
        url=f"{router_config.data_interface_service_url}/forecast/fetch",
        headers={"X-Hotel-Id": str(hotel.id)},
        json=req.model_dump(mode="json"),
    )
    forward_response(source=forecast_response, target=response)

    logger.info(
        "Прогноз успешно получен через router_service: hotel_id=%s, horizon=%s",
        hotel.id,
        req.horizon,
    )
    return response
