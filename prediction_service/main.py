import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session

from prediction_service.core.model_loader import load_model_and_config
from prediction_service.core.forecast import run_forecast_for_hotel
from prediction_service.core.trainer import train_model_for_hotel, setup_hotel_model_from_base
from prediction_service.config import MODEL_DIR
from prediction_service.schemas import (
    TrainRequest, TrainResponse,
    InitHotelResponse,
    ModelStatusResponse, ModelConfigResponse,
    PredictRequest, PredictResponse
)

from shared.db import get_sync_session
from shared.models import Prediction
from shared.errors import (
    register_error_handlers,
    setup_openapi_with_errors,register_errors,
    ServiceError, ValidationError,
    ModelConfigError, ModelNotFoundError,
    ExternalServiceError, DatabaseError,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_error_handlers(app)
    setup_openapi_with_errors(app)
    yield


app = FastAPI(title="Prediction Service API", lifespan=lifespan)


@app.post(
    "/run-predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK
)
@register_errors(
    ModelNotFoundError, ModelConfigError,
    ValidationError, ServiceError, DatabaseError
)
def predict(
        req: PredictRequest,
        db: Session = Depends(get_sync_session)
) -> PredictResponse:
    """
    Запускает прогнозирование для указанного отеля.
    """
    result = run_forecast_for_hotel(
        req.hotel_id, db, req.target_date, has_deposit=req.has_deposit
    )

    # Сохраняем прогноз в БД
    predictions = [
        Prediction(
            hotel_id=result["hotel_id"],
            target_date=datetime.fromisoformat(day["date"]).date(),
            has_deposit=req.has_deposit,
            bookings=day["bookings"],
            cancellations=day["cancellations"],
        )
        for day in result["forecast"]
    ]

    try:
        db.bulk_save_objects(predictions)
        db.commit()
        logger.info(f"Прогноз сохранён: {len(predictions)} записей для hotel_id={req.hotel_id}")
    except Exception as e:
        db.rollback()
        logger.exception("Ошибка при сохранении прогноза в БД: %s", e)
        raise DatabaseError("Ошибка при сохранении прогноза в базу данных")

    return PredictResponse(**result)


@app.post(
    "/train",
    response_model=TrainResponse,
    status_code=status.HTTP_202_ACCEPTED
)
@register_errors(ServiceError)
def train(
        req: TrainRequest,
        db: Session = Depends(get_sync_session)
) -> TrainResponse:
    """
    Обучает или дообучает модель для отеля.
    """
    if req.init:
        setup_hotel_model_from_base(req.hotel_id)

    train_model_for_hotel(
        hotel_id=req.hotel_id,
        db_session=db,
        epochs=req.epochs,
        batch_size=req.batch_size,
    )
    return TrainResponse(
        hotel_id=req.hotel_id,
        message="Model fine-tuned and saved",
    )


@app.post(
    "/init_hotel/{hotel_id}",
    response_model=InitHotelResponse,
    status_code=status.HTTP_201_CREATED
)
@register_errors(ServiceError)
def init_hotel(hotel_id: int):
    """
    Инициализирует директорию модели для нового отеля.
    """
    logger.info(f"Инициализация модели для отеля {hotel_id}")
    setup_hotel_model_from_base(hotel_id)
    return InitHotelResponse(
        hotel_id=hotel_id,
        path=str(MODEL_DIR / f"hotel_{hotel_id}"),
    )


@app.get(
"/status/{hotel_id}",
     response_model=ModelStatusResponse,
     status_code=status.HTTP_200_OK
)
def check_model_status(hotel_id: int) -> ModelStatusResponse:
    """
    Проверяет наличие модели и её конфигурации.
    """
    model_path = MODEL_DIR / f"hotel_{hotel_id}/model.pt"
    config_path = MODEL_DIR / f"hotel_{hotel_id}/model_config.json"

    return ModelStatusResponse(
        hotel_id=hotel_id,
        model_exists=model_path.exists(),
        config_exists=config_path.exists(),
    )

@app.get(
    "/config/{hotel_id}",
    response_model=ModelConfigResponse,
    status_code=status.HTTP_200_OK
)
@register_errors(
    ServiceError, ExternalServiceError,
    ModelNotFoundError, ModelConfigError
)
def get_model_config(hotel_id: int) -> ModelConfigResponse:
    """
    Возвращает конфигурацию модели, включая структуру признаков и гиперпараметры.
    """
    logger.info(f"Запрос конфигурации модели для отеля {hotel_id}")
    _, config = load_model_and_config(hotel_id)
    return ModelConfigResponse(hotel_id=hotel_id, config=config)
