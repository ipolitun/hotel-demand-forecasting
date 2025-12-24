import logging

import httpx
from fastapi import APIRouter, Depends, status, Response

from router.api.dependencies import get_http_client
from router.api.schemas import PredictRequest, PredictResponse
from router.api.utils.http import proxy_post, forward_response
from router.config import router_config
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
        response: Response,
        client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Прокси-запрос в prediction_service.
    Использует общий асинхронный httpx.AsyncClient.
    """
    logger.info("Вызов run_prediction: %s", req.model_dump())

    predict_response = await proxy_post(
        client=client,
        url=f"{router_config.prediction_service_url}/run-predict",
        json=req.model_dump(mode="json"),
        timeout=10,
    )

    forward_response(source=predict_response, target=response)

    logger.info(
        "Прогноз успешно получен через router_service: hotel_id=%s, target_date=%s",
        req.hotel_id,
        req.target_date,
    )
    return response
