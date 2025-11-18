import logging
import httpx
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from router.config import router_config
from router.schemas import PredictRequest, PredictResponse
from router.dependencies import get_http_client

from shared.errors import (
    register_errors,
    ValidationError,
    ExternalServiceError,
    ModelConfigError,
    ModelNotFoundError,
    ServiceError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/run-prediction",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Запуск прогноза для отеля",
    response_description="Возвращает прогноз спроса и отмен для заданной даты",
)
@register_errors(
    ValidationError, ExternalServiceError,
    ModelConfigError, ModelNotFoundError, ServiceError,
)
async def run_prediction(
    req: PredictRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос в prediction_service.
    Использует общий асинхронный httpx.AsyncClient.
    """
    try:
        logger.info("Вызов run_prediction: %s", req.model_dump())

        response = await client.post(
            f"{router_config.prediction_service_url}/run-predict",
            json=req.model_dump(mode="json"),
            timeout=10,
        )

        result = response.json()

    except httpx.RequestError as e:
        logger.error("Ошибка соединения с prediction_service: %s", e)
        raise ExternalServiceError("Сервис прогнозирования недоступен")

    except ValueError as e:
        logger.exception("Ошибка при парсинге ответа prediction_service: %s", e)
        raise ExternalServiceError("Некорректный ответ от prediction_service")

    if response.status_code != status.HTTP_200_OK:
        if isinstance(result, dict) and "error" in result:
            # Проксируем JSON-ошибку без изменений
            return JSONResponse(status_code=response.status_code, content=result)
        logger.error("Неожиданный ответ prediction_service: %s", result)
        raise ExternalServiceError("Некорректный формат ответа prediction_service")

    logger.info(
        "Прогноз успешно получен через router_service: hotel_id=%s, target_date=%s",
        req.hotel_id,
        req.target_date,
    )
    return result
