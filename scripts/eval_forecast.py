"""
Скрипт для оценки качества прогноза модели.

Сравнивает предсказанные значения бронирований и отмен
с фактическими данными из БД и считает метрики (RMSE, MAE, MAPE, R²).

Используется для проверки и демонстрации.
"""

import logging
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from prediction_service.core.forecast import run_forecast_for_hotel
from shared.db_models import Booking
from shared.db import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Метрики
def evaluate(y_true, y_pred):
    """
    Считает RMSE, MAE, MAPE и R².
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(
        np.abs((np.array(y_true) - np.array(y_pred)) / np.maximum(1, np.array(y_true)))
    ) * 100
    r2 = r2_score(y_true, y_pred)
    return rmse, mae, mape, r2


def evaluate_forecast(hotel_id: int, has_deposit: bool, start_date: date, db: Session):
    """
    Запускает прогноз и сравнивает его с фактами.
    """
    logger.info(f"Запуск прогноза для hotel_id={hotel_id}, start_date={start_date}, deposit={has_deposit}")

    forecast = run_forecast_for_hotel(hotel_id, db, start_date, has_deposit)
    predicted = forecast["forecast"]

    bookings_true, cancellations_true, dates = [], [], []

    for item in predicted:
        arrival_date = date.fromisoformat(item["date"])
        dates.append(arrival_date)

        bookings = db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.arrival_date == arrival_date,
            Booking.has_deposit == has_deposit
        ).count()

        cancellations = db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.arrival_date == arrival_date,
            Booking.has_deposit == has_deposit,
            Booking.is_cancellation.is_(True)
        ).count()

        bookings_true.append(bookings)
        cancellations_true.append(cancellations)

    bookings_pred = [x["bookings"] for x in predicted]
    cancellations_pred = [x["cancellations"] for x in predicted]

    # Метрики
    short_range = slice(0, 7)    # 1–7 дней
    mid_range = slice(7, 30)     # 8–30 дней

    def log_metrics(label, y_true, y_pred):
        rmse, mae, mape, r2 = evaluate(y_true, y_pred)
        logger.info(f"{label} — RMSE={rmse:.2f}, MAE={mae:.2f}, MAPE={mape:.2f}%, R²={r2:.4f}")

    logger.info("Метрики для бронирований:")
    log_metrics("  1–7 дней", bookings_true[short_range], bookings_pred[short_range])
    log_metrics("  8–30 дней", bookings_true[mid_range], bookings_pred[mid_range])

    logger.info("Метрики для отмен:")
    log_metrics("  1–7 дней", cancellations_true[short_range], cancellations_pred[short_range])
    log_metrics("  8–30 дней", cancellations_true[mid_range], cancellations_pred[mid_range])

    # Таблица результатов
    df_result = pd.DataFrame({
        "Дата": dates,
        "Прогноз бронирований": bookings_pred,
        "Факт бронирований": bookings_true,
        "Прогноз отмен": cancellations_pred,
        "Факт отмен": cancellations_true
    })

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    output_file = results_dir / f"forecast_eval_hotel{hotel_id}.csv"
    df_result.to_csv(output_file, index=False, encoding="utf-8")

    logger.info(f"Результаты сохранены в {output_file}")


def main():
    hotel_id = 1
    has_deposit = False
    start_date = date(2017, 7, 1)

    with SessionLocal() as session:
        evaluate_forecast(hotel_id, has_deposit, start_date, session)


if __name__ == "__main__":
    main()
