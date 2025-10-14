import logging
from datetime import timedelta, date
import numpy as np
import pandas as pd
import torch
from sqlalchemy.orm import Session

from shared.db import get_sync_session
from shared.data_loader import load_bookings, load_weather, load_holidays
from shared.models import Hotel
from shared.errors import (
    ModelConfigError,
    ValidationError,
    ServiceError,
)
from prediction_service.core.model_loader import load_model_and_config
from prediction_service.preprocessing.preprocessor import preprocess_data
from prediction_service.preprocessing.scaling import normalize_data, denormalize_forecast

logger = logging.getLogger(__name__)

session = get_sync_session()

def aggregate_forecast_inputs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегирует входные данные по дате: усреднение числовых и мода категориальных признаков.

    Returns:
        pd.DataFrame: агрегированные по датам данные.
    """
    agg_df = df.groupby('arrival_date').agg({
        col: 'mean'
        for col in df.columns if col not in [
            'arrival_date', 'day_of_week',
            'market_segment_enc', 'distribution_channel_enc',
            'reserved_room_type_enc'
        ]
    }).reset_index()

    # Категориальные — берём моду
    for cat_col in ['day_of_week', 'market_segment_enc',
                    'distribution_channel_enc', 'reserved_room_type_enc']:
        mode_vals = df.groupby('arrival_date')[cat_col].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
        )
        agg_df[cat_col] = mode_vals.values

    return agg_df


def process_inputs_for_model(
    hotel_id: int, db: Session, config: dict,
    target_date: date, has_deposit: bool
) -> np.ndarray:
    """
    Загружает и подготавливает входные данные для модели.

    Returns:
        np.ndarray: массив входных признаков формы [horizon, num_features].
    """
    logger.info(f"Подготовка входных данных: hotel_id={hotel_id}, target_date={target_date}, has_deposit={has_deposit}")

    try:
        df_b = load_bookings(hotel_id, db)
        df_b = df_b[df_b['has_deposit'] == has_deposit]
        df_w = load_weather(hotel_id, db)
        df_h = load_holidays(db)
        hotel = db.query(Hotel).get(hotel_id)
    except Exception as e:
        logger.error("Ошибка при загрузке данных: %s", e)
        raise ServiceError("Ошибка загрузки данных для прогноза")

    # Преобразование дат
    for col in ['arrival_date']:
        df_b[col] = pd.to_datetime(df_b[col], errors='coerce')
    df_w['date'] = pd.to_datetime(df_w['date'], errors='coerce')
    df_h['date'] = pd.to_datetime(df_h['date'], errors='coerce')

    # Очистка
    df_b.drop(columns=["booking_ref", "created_at"], inplace=True, errors="ignore")
    df_h.drop(columns=["region", "created_at"], inplace=True, errors="ignore")

    # Объединение с погодой
    df = df_b.merge(df_w, left_on='arrival_date', right_on='date',
                    how='left', suffixes=('', '_weather'))

    # Ограничение диапазона (последние 30 дней)
    start_date = target_date - timedelta(days=29)
    df = df[(df["arrival_date"].dt.date >= start_date) & (df["arrival_date"].dt.date <= target_date)]
    if df.empty:
        raise ValidationError(f"Нет данных о бронированиях {start_date} – {target_date}")

    # Добавление признаков
    df['is_holiday'] = df['arrival_date'].isin(df_h['date']).astype(int)
    df['is_city_hotel'] = int(hotel.is_city_hotel)
    df = preprocess_data(df, hotel_id)

    # Нормализация
    df = normalize_data(df, hotel_id)

    # Проверка на признаки
    numeric_features = config["numeric_features"]
    categorical_features = config["categorical_features"]
    missing = [col for col in numeric_features + categorical_features if col not in df.columns]
    if missing:
        raise ModelConfigError(f"В данных отсутствуют признаки: {missing}")

    # Агрегация по датам
    df = aggregate_forecast_inputs(df)

    # Проверка количества дней
    if len(df) < config["forecast_horizon"]:
        raise ValidationError(f"Недостаточно дней: {len(df)} < {config['forecast_horizon']}")

    df = df.sort_values('arrival_date')

    # Формирование входов
    numeric_ordered = df[numeric_features].values
    categorical_ordered = df[categorical_features].values
    X_combined = np.concatenate([numeric_ordered, categorical_ordered], axis=1)

    return X_combined[-config["forecast_horizon"]:]  # [horizon, dim]


def run_forecast_for_hotel(
    hotel_id: int, db: Session, target_date: date, has_deposit: bool
) -> dict:
    """
    Запускает прогноз для отеля.
    """
    logger.info(f"Запуск прогноза: hotel_id={hotel_id}, target_date={target_date}, has_deposit={has_deposit}")

    model, config = load_model_and_config(hotel_id)

    # Подготовка входов
    X = process_inputs_for_model(hotel_id, db, config, target_date, has_deposit)

    expected_dim = config["num_numeric_features"] + len(config["categorical_features"])
    if X.shape[1] != expected_dim:
        raise ModelConfigError(f"Ожидалось {expected_dim} признаков, получено {X.shape[1]}")

    num_feats = config["numeric_features"]
    cat_feats = config["categorical_features"]

    X_numeric = X[:, :len(num_feats)]
    X_categorical = X[:, len(num_feats):]

    x_cat_dict = {
        feat: torch.tensor(X_categorical[:, idx], dtype=torch.long).unsqueeze(0)
        for idx, feat in enumerate(cat_feats)
    }
    x_numeric_tensor = torch.tensor(X_numeric, dtype=torch.float32).unsqueeze(0)

    try:
        with torch.no_grad():
            y_pred = model(x_numeric_tensor, x_cat_dict).squeeze(0).numpy()
    except Exception as e:
        raise ServiceError(f"Ошибка при выполнении прогноза: {e}")

    y_pred = denormalize_forecast(y_pred, hotel_id)

    forecast = [
        {
            "date": (target_date + timedelta(days=i)).isoformat(),
            "bookings": int(round(book)),
            "cancellations": int(round(cancel)),
        }
        for i, (book, cancel) in enumerate(y_pred)
    ]

    logger.info(f"Прогноз завершён: {len(forecast)} дней")

    return {
        "hotel_id": hotel_id,
        "target_date": target_date.isoformat(),
        "forecast": forecast,
    }
