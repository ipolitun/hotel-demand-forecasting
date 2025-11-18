import logging
import httpx
from typing import Dict
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import JSONResponse

from router.config import router_config
from router.schemas import ForecastRequest, ForecastResponse, BookingImportResponse
from router.dependencies import verify_token, get_http_client

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
    file: UploadFile = File(...),
    token_data: Dict = Depends(verify_token),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос для загрузки бронирований.
    Отправляет CSV-файл в `data_interface_service/booking/import`.
    """
    hotel_id = token_data.get("hotel_id")
    if not hotel_id:
        logger.warning("Попытка импорта без hotel_id в токене")
        raise AuthorizationError("Отсутствует hotel_id в токене")

    file_content = await file.read()
    files = {"file": (file.filename, file_content, file.content_type)}
    headers = {"X-Hotel-Id": int(hotel_id)}

    try:
        response = await client.post(
            f"{router_config.data_interface_service_url}/booking/import",
            files=files,
            headers=headers,
        )
        result = response.json()
    except httpx.RequestError as e:
        logger.error("Ошибка соединения с data_interface_service: %s", e)
        raise ExternalServiceError("Сервис импорта недоступен")
    except Exception as e:
        logger.exception("Ошибка при парсинге ответа data_interface_service: %s", e)
        raise ExternalServiceError("Некорректный ответ от data_interface_service")

    if response.status_code != status.HTTP_201_CREATED:
        if result.get("error"):
            # Проксируем ошибку data_interface_service без изменений
            return JSONResponse(status_code=response.status_code, content=result)

        logger.error("Неожиданный ответ от data_interface_service: %s", result)
        raise ExternalServiceError("Некорректный формат ответа data_interface_service")

    logger.info(
        "Импорт завершён через router_service: hotel_id=%s, добавлено=%s, дубликатов=%s",
        hotel_id,
        result.get("added"),
        result.get("duplicates_skipped"),
    )
    return result


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
    token_data: Dict = Depends(verify_token),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос для получения прогноза.
    Перенаправляет вызов в `data_interface_service/forecast/fetch`.
    """
    hotel_id = token_data.get("hotel_id")
    if not hotel_id:
        logger.warning("Попытка получения прогноза без hotel_id в токене")
        raise AuthorizationError("Отсутствует hotel_id в токене")
    headers = {"X-Hotel-Id": int(hotel_id)}

    try:
        response = await client.post(
            f"{router_config.data_interface_service_url}/forecast/fetch",
            json=req.model_dump(mode="json"),
            headers=headers,
        )
        result = response.json()
    except httpx.RequestError as e:
        logger.error("Ошибка соединения с data_interface_service: %s", e)
        raise ExternalServiceError("Прогноз недоступен")
    except Exception as e:
        logger.exception("Ошибка при парсинге ответа data_interface_service: %s", e)
        raise ExternalServiceError("Некорректный ответ от data_interface_service")

    if response.status_code != status.HTTP_200_OK:
        if result.get("error"):
            # Проксируем ошибку data_interface_service без изменений
            return JSONResponse(status_code=response.status_code, content=result)

        logger.error("Неожиданный ответ от data_interface_service: %s", result)
        raise ExternalServiceError("Некорректный формат ответа data_interface_service")

    logger.info(
        "Прогноз успешно получен через router_service: hotel_id=%s, horizon=%s",
        hotel_id,
        req.horizon,
    )
    return result
