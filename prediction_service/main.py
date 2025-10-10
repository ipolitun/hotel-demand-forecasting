import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from core.model_loader import load_model_and_config
from core.forecast import run_forecast_for_hotel
from core.trainer import train_model_for_hotel, setup_hotel_model_from_base
from prediction_service.schemas import (
    TrainRequest, InitHotelRequest,
    PredictRequest, PredictResponse
)
from prediction_service.config import MODEL_DIR
from shared.db import get_sync_session
from shared.models import Prediction

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Prediction Service API")


@app.post("/run-predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_sync_session)):
    """
    Запускает прогнозирование для указанного отеля.
    """
    try:
        logger.info(f"Получен запрос: {req.json()}")

        result = run_forecast_for_hotel(
            req.hotel_id, db, req.target_date, has_deposit=req.has_deposit
        )

        # Сохраняем прогноз в БД
        predictions = []
        for day in result.forecast:
            forecast_date = (
                datetime.strptime(day.date, "%Y-%m-%d").date()
                if isinstance(day.date, str) else day.date
            )
            predictions.append(
                Prediction(
                    hotel_id=req.hotel_id,
                    target_date=forecast_date,
                    has_deposit=req.has_deposit,
                    bookings=day.bookings,
                    cancellations=day.cancellations,
                )
            )
        db.bulk_save_objects(predictions)
        db.commit()
        logger.info(f"Прогноз сохранён: {len(result.forecast)} записей")

        return result

    except ValueError as ve:
        logger.error(f"Ошибка данных: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        db.rollback()
        logger.exception("Внутренняя ошибка при прогнозировании")
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/train")
def train(req: TrainRequest, db: Session = Depends(get_sync_session)):
    """
    Обучает или дообучает модель для отеля.
    """
    try:
        logger.info(f"Запрос на обучение модели: {req.json()}")
        if req.init:
            setup_hotel_model_from_base(req.hotel_id)

        train_model_for_hotel(
            hotel_id=req.hotel_id,
            db_session=db,
            epochs=req.epochs,
            batch_size=req.batch_size,
        )
        return {
            "hotel_id": req.hotel_id,
            "status": "success",
            "message": "Model fine-tuned and saved",
        }
    except Exception as e:
        logger.exception("Ошибка при обучении модели")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/init_hotel")
def init_hotel(req: InitHotelRequest):
    """
    Инициализирует директорию модели для нового отеля.
    """
    try:
        logger.info(f"Инициализация модели для отеля {req.hotel_id}")
        setup_hotel_model_from_base(req.hotel_id)
        return {
            "status": "initialized",
            "hotel_id": req.hotel_id,
            "path": str(MODEL_DIR / f"hotel_{req.hotel_id}"),
        }
    except Exception as e:
        logger.exception("Ошибка при инициализации модели")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{hotel_id}")
def check_model_status(hotel_id: int):
    """
    Проверяет наличие модели и её конфигурации.
    """
    model_path = MODEL_DIR / f"hotel_{hotel_id}/model.pt"
    config_path = MODEL_DIR / f"hotel_{hotel_id}/model_config.json"
    logger.info(f"Проверка статуса модели: hotel_id={hotel_id}")
    return {
        "hotel_id": hotel_id,
        "model_exists": model_path.exists(),
        "config_exists": config_path.exists(),
    }


@app.get("/config/{hotel_id}")
def get_model_config(hotel_id: int):
    """
    Возвращает конфигурацию модели для отеля.
    """
    try:
        logger.info(f"Запрос конфигурации модели для отеля {hotel_id}")
        _, config = load_model_and_config(hotel_id)
        return config
    except Exception as e:
        logger.exception("Ошибка при загрузке конфигурации")
        raise HTTPException(status_code=500, detail=str(e))
