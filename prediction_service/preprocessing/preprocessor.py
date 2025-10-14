import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import logging

from shared.errors import (
    ServiceError,
    ValidationError,
    MappingError,
    ModelConfigError,
)

logger = logging.getLogger(__name__)

# Соответствие: имя сохранённого энкодера -> оригинальная колонка
ENCODING_MAP = {
    "market_segment_enc": "market_segment",
    "distribution_channel_enc": "distribution_channel",
    "reserved_room_type_enc": "reserved_room_type",
}


def load_encoder(name: str, hotel_id: int):
    """
    Загружает сохранённый LabelEncoder для конкретного отеля.
    """
    path = Path(f"prediction_service/models/hotel_{hotel_id}/encoders") / f"{name}.pkl"
    logger.debug(f"Загрузка энкодера {name}: {path}")

    if not path.exists():
        logger.error(f"Энкодер не найден: {path}")
        raise ModelConfigError(f"Энкодер {name} отсутствует для hotel_id={hotel_id}")

    try:
        return joblib.load(path)
    except Exception as e:
        logger.exception(f"Ошибка при загрузке энкодера {name}: {e}")
        raise ModelConfigError(f"Ошибка при загрузке энкодера {name}: {e}")


def encode_categorical_features(df: pd.DataFrame, hotel_id: int) -> pd.DataFrame:
    """
    Применяет сохранённые энкодеры к категориальным колонкам.
    """
    for enc_col, orig_col in ENCODING_MAP.items():
        if orig_col not in df.columns:
            logger.warning(f"Отсутствует колонка {orig_col} для кодирования ({enc_col})")
            raise MappingError(f"Отсутствует колонка {orig_col} для кодирования")

        encoder = load_encoder(enc_col, hotel_id)

        try:
            df[enc_col] = encoder.transform(df[orig_col].astype(str))
        except Exception as e:
            logger.exception(f"Ошибка кодирования колонки {orig_col}: {e}")
            raise MappingError(f"Ошибка при кодировании колонки {orig_col}: {e}")

    df.drop(columns=list(ENCODING_MAP.values()), inplace=True, errors="ignore")
    logger.debug("Категориальные признаки закодированы")
    return df


def preprocess_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Приводит колонку arrival_date к datetime и проверяет корректность.
    """
    try:
        if not np.issubdtype(df['arrival_date'].dtype, np.datetime64):
            logger.debug("Преобразование arrival_date в datetime")
            df['arrival_date'] = pd.to_datetime(df['arrival_date'], errors='coerce')

        invalid_dates = df['arrival_date'].isna().sum()
        if invalid_dates > 0:
            raise ValidationError(f"Обнаружено {invalid_dates} некорректных дат в arrival_date")
        return df
    except Exception as e:
        logger.exception("Ошибка при обработке даты прибытия")
        raise ValidationError(f"Ошибка при обработке даты прибытия: {e}")


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет derived-признаки.
    """
    try:
        df['lead_time_log'] = np.log1p(df['lead_time'])
        logger.debug("Добавлен признак lead_time_log")
        return df
    except Exception as e:
        logger.exception("Ошибка при создании производных признаков")
        raise ServiceError(f"Ошибка при добавлении признаков: {e}")


def check_missing_for_aggregation(df: pd.DataFrame):
    """
    Проверяет наличие пропусков в arrival_date и is_cancellation.
    """
    if df[['arrival_date', 'is_cancellation']].isnull().any().any():
        logger.error("Пропущенные значения в arrival_date или is_cancellation")
        raise ValidationError("Пропущенные значения в arrival_date или is_cancellation")


def aggregate_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Формирует признаки на основе статистик прошлого года и усреднённых значений по дню и месяцу.

    Returns:
        pd.DataFrame: DataFrame с агрегированными признаками.
    """
    logger.info("Начало агрегации исторических признаков")

    daily = df.groupby('arrival_date').agg(
        bookings=('is_cancellation', 'count'),
        cancels=('is_cancellation', 'sum')
    ).reset_index()

    # Усреднённые значения по комбинации (месяц, день)
    daily['day'] = daily['arrival_date'].dt.day
    daily['month'] = daily['arrival_date'].dt.month
    mean_by_day_month = (
        daily.groupby(['month', 'day'])[['bookings', 'cancels']]
        .mean()
        .reset_index()
        .rename(columns={'bookings': 'bookings_avg', 'cancels': 'cancels_avg'})
    )

    # Лагированные признаки (значения на год назад)
    daily['arrival_date_last_year'] = daily['arrival_date'] + pd.DateOffset(years=1)
    lagged = daily[['arrival_date_last_year', 'bookings', 'cancels']].rename(columns={
        'arrival_date_last_year': 'arrival_date',
        'bookings': 'bookings_last_year',
        'cancels': 'cancels_last_year'
    })

    enriched = df.merge(lagged, on='arrival_date', how='left')
    enriched['day'] = enriched['arrival_date'].dt.day
    enriched['month'] = enriched['arrival_date'].dt.month
    enriched = enriched.merge(mean_by_day_month, on=['month', 'day'], how='left')

    # Замена пропусков усреднёнными значениями
    enriched['bookings_last_year'] = enriched['bookings_last_year'].fillna(enriched['bookings_avg'])
    enriched['cancels_last_year'] = enriched['cancels_last_year'].fillna(enriched['cancels_avg'])

    enriched.drop(columns=['day', 'month', 'bookings_avg', 'cancels_avg'], inplace=True)
    logger.debug("Агрегация завершена")
    return enriched


def drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Удаляет служебные колонки, которые не нужны для модели.
    """
    columns_to_drop = ['_sa_instance_state', 'hotel_id']
    df.drop(columns=columns_to_drop, inplace=True, errors="ignore")
    logger.debug(f"Удалены колонки: {columns_to_drop}")
    return df


def enforce_numeric_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Приводит числовые признаки к float/int.
    """
    numeric_cols = [
        "adr", "lead_time", "lead_time_log", "total_guests",
        "total_nights", "booking_changes", "temp_avg",
        "bookings_last_year", "cancels_last_year"
    ]
    try:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        logger.debug("Числовые признаки приведены к numeric")
        return df
    except Exception as e:
        raise ValidationError(f"Ошибка при приведении типов: {e}")


def preprocess_data(df: pd.DataFrame, hotel_id: int) -> pd.DataFrame:
    """
    Полный пайплайн предобработки данных.

    Returns:
        pd.DataFrame: предобработанные данные для модели.
    """
    if df.empty:
        raise ValidationError("Пустой DataFrame для предобработки")

    df = drop_irrelevant_columns(df)
    df = enforce_numeric_types(df)
    df = encode_categorical_features(df, hotel_id)
    df = preprocess_dates(df)
    df = add_derived_features(df)

    check_missing_for_aggregation(df)
    df = aggregate_historical_features(df)

    if df.isnull().sum().sum() > 0:
        logger.warning("Есть пропущенные значения после агрегации")
        df.ffill(inplace=True)
        logger.debug("Выполнен forward fill для NaN")
    else:
        logger.debug("Пропусков нет")

    logger.info(f"Финальные признаки: {df.columns.tolist()}")
    return df
