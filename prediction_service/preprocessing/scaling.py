import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
import logging

from shared.errors import (
    ValidationError,
    ModelConfigError,
    ServiceError,
)

logger = logging.getLogger(__name__)

SCALE_FEATURES = [
    'lead_time', 'lead_time_log', 'adr', 'total_guests',
    'total_nights', 'temp_avg', 'bookings_last_year',
    'cancels_last_year', 'booking_changes'
]


def load_scaler(hotel_id: int) -> MinMaxScaler:
    """
    Загружает MinMaxScaler для указанного отеля.
    """
    path = Path(f"prediction_service/models/hotel_{hotel_id}/scalers/feature_scaler.pkl")
    logger.debug(f"Загрузка scaler: {path}")

    if not path.exists():
        logger.error(f"Scaler отсутствует: {path}")
        raise ModelConfigError(f"Scaler не найден для hotel_id={hotel_id}")

    try:
        scaler = joblib.load(path)
        logger.debug(f"Scaler успешно загружен для hotel_id={hotel_id}")
        return scaler
    except Exception as e:
        logger.exception(f"Ошибка при загрузке scaler: {e}")
        raise ModelConfigError(f"Ошибка при загрузке scaler: {e}")


def normalize_data(df: pd.DataFrame, hotel_id: int) -> pd.DataFrame:
    """
    Применяет min-max нормализацию к числовым признакам.
    """
    if df.empty:
        logger.error("Получен пустой DataFrame для нормализации")
        raise ValidationError("Пустой DataFrame для нормализации")

    scaler = load_scaler(hotel_id)
    df = df.copy()

    for feat in SCALE_FEATURES:
        if feat in df.columns:
            try:
                idx = list(scaler.feature_names_in_).index(feat)
                min_val = scaler.data_min_[idx]
                scale = scaler.scale_[idx]
                df[feat] = (df[feat] - min_val) * scale
            except ValueError:
                logger.error(f"Признак '{feat}' отсутствует в scaler")
                raise ModelConfigError(f"Признак '{feat}' отсутствует в scaler для hotel_id={hotel_id}")
            except Exception as e:
                logger.exception(f"Ошибка при нормализации признака '{feat}': {e}")
                raise ServiceError(f"Ошибка при нормализации признака '{feat}': {e}")

    logger.debug("Нормализация завершена успешно")
    return df


def denormalize_forecast(y_pred: np.ndarray, hotel_id: int) -> np.ndarray:
    """
    Обратная нормализация предсказаний модели (bookings, cancellations).
    """
    if y_pred is None or y_pred.size == 0:
        logger.error("Получен пустой массив предсказаний для денормализации")
        raise ValidationError("Пустой массив предсказаний для денормализации")

    scaler = load_scaler(hotel_id)

    try:
        feature_names = scaler.feature_names_in_
        horizon = y_pred.shape[0]

        # Создаём временный DataFrame для inverse_transform
        fake_df = pd.DataFrame(data=np.zeros((1, len(feature_names))), columns=feature_names)
        for i in range(horizon):
            fake_df[f"book_d{i + 1}"] = y_pred[i, 0]
            fake_df[f"cancel_d{i + 1}"] = y_pred[i, 1]

        denorm_df = scaler.inverse_transform(fake_df)

        # Извлекаем восстановленные значения
        denorm_pred = np.zeros_like(y_pred)
        for i in range(horizon):
            denorm_pred[i, 0] = denorm_df[0, feature_names.tolist().index(f"book_d{i + 1}")]
            denorm_pred[i, 1] = denorm_df[0, feature_names.tolist().index(f"cancel_d{i + 1}")]

        logger.debug("Денормализация предсказаний завершена")
        return denorm_pred

    except Exception as e:
        logger.exception(f"Ошибка при денормализации прогноза: {e}")
        raise ServiceError(f"Ошибка при денормализации прогноза: {e}")