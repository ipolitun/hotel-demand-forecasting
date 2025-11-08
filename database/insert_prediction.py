"""
Вставка демонстрационных прогнозов в таблицу Prediction.

Генерирует предсказания на основе исторических данных с добавлением
случайного шума (нормального распределения) и записывает их в базу данных.
"""

from datetime import datetime, date
import numpy as np
from sqlalchemy.orm import Session

from shared.db import get_sync_session
from shared.models import Prediction


# === Исторические данные для примера ===
HISTORY = [
    ("2017-07-10", 122, 46), ("2017-07-11", 102, 35), ("2017-07-12", 101, 25),
    ("2017-07-13", 148, 41), ("2017-07-14", 70, 26), ("2017-07-15", 191, 75),
    ("2017-07-16", 98, 28), ("2017-07-17", 125, 47), ("2017-07-18", 87, 23),
    ("2017-07-19", 60, 13), ("2017-07-20", 86, 29), ("2017-07-21", 93, 29),
    ("2017-07-22", 139, 41), ("2017-07-23", 84, 25), ("2017-07-24", 135, 42),
    ("2017-07-25", 87, 25), ("2017-07-26", 95, 32), ("2017-07-27", 104, 40),
    ("2017-07-28", 100, 50), ("2017-07-29", 135, 58), ("2017-07-30", 78, 25),
    ("2017-07-31", 116, 39), ("2017-08-01", 93, 38), ("2017-08-02", 106, 33),
    ("2017-08-03", 123, 44), ("2017-08-04", 97, 28), ("2017-08-05", 80, 29),
    ("2017-08-06", 74, 26), ("2017-08-07", 118, 37), ("2017-08-08", 80, 34),
]

# === Средняя абсолютная ошибка (MAE) по разным горизонтам ===
MAE = {
    "bookings_1_7": 15.08,
    "cancellations_1_7": 12.82,
    "bookings_8_30": 22.54,
    "cancellations_8_30": 19.78,
}


def generate_predictions() -> list[dict]:
    """
    Создаёт синтетические предсказания с добавлением шума.
    Возвращает список словарей с датой, прогнозами и реальными значениями.
    """
    predictions = []

    for i, (date_str, true_bookings, true_cancellations) in enumerate(HISTORY):
        day_idx = i + 1
        is_short_term = day_idx <= 7

        err_b = MAE["bookings_1_7"] if is_short_term else MAE["bookings_8_30"]
        err_c = MAE["cancellations_1_7"] if is_short_term else MAE["cancellations_8_30"]

        pred_bookings = max(0, round(np.random.normal(loc=true_bookings, scale=err_b)))
        pred_cancellations = max(0, round(np.random.normal(loc=true_cancellations, scale=err_c)))

        predictions.append({
            "target_date": datetime.strptime(date_str, "%Y-%m-%d").date(),
            "bookings": pred_bookings,
            "cancellations": pred_cancellations,
        })

    return predictions


def insert_predictions(hotel_id: int, has_deposit: bool, db: Session) -> int:
    """
    Вставляет сгенерированные прогнозы в таблицу Prediction.
    Возвращает количество добавленных записей.
    """
    records = generate_predictions()

    objects = [
        Prediction(
            hotel_id=hotel_id,
            has_deposit=has_deposit,
            target_date=entry["target_date"],
            bookings=entry["bookings"],
            cancellations=entry["cancellations"],
        )
        for entry in records
    ]

    db.add_all(objects)
    db.commit()

    print(f"Добавлено {len(objects)} записей в таблицу prediction для hotel_id={hotel_id}")
    return len(objects)


def main() -> None:
    """Точка входа для одиночного запуска скрипта."""
    hotel_id = 1
    has_deposit = False

    with get_sync_session() as db:
        insert_predictions(hotel_id, has_deposit, db)


if __name__ == "__main__":
    main()
