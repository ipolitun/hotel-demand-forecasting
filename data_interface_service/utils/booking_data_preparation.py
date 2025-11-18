import asyncio
import csv
from io import StringIO
import logging

import pandas as pd

from data_interface_service.utils.date_parsing import parse_dates_vectorized
from data_interface_service.utils.booking_constants import (
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    AGGREGATES,
)
from shared.errors import CSVProcessingError

logger = logging.getLogger(__name__)


# === CSV: чтение и подготовка ===

def detect_separator(content: str) -> str:
    """Определяет наиболее вероятный разделитель CSV-файла."""
    sample = content[:2000]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,").delimiter
    except Exception:
        return ";" if sample.count(";") > sample.count(",") else ","


def read_csv_to_dataframe(content: str) -> pd.DataFrame:
    """Читает CSV в DataFrame с автоопределением разделителя."""
    try:
        sep = detect_separator(content)
        df = pd.read_csv(StringIO(content), sep=sep)
    except Exception:
        logger.exception("Ошибка чтения CSV")
        raise CSVProcessingError("Ошибка чтения CSV (неверный формат или разделитель).")

    if df.empty:
        raise CSVProcessingError("Файл пуст.")

    logger.debug("CSV успешно прочитан: %s строк, %s колонок", df.shape[0], df.shape[1])
    return df


# === Валидация и нормализация ===

def validate_booking_columns(df: pd.DataFrame) -> None:
    """Проверяет наличие обязательных колонок для бронирований."""
    if not (
            "arrival_date" in df.columns or
            all(c in df.columns for c in ["arrival_date_year", "arrival_date_month", "arrival_date_day_of_month"])
    ):
        raise CSVProcessingError(
            "Отсутствует дата прибытия — используйте 'arrival_date' или три поля: "
            "'arrival_date_year', 'arrival_date_month', 'arrival_date_day_of_month'."
        )

    required_columns = ["is_cancellation", "has_deposit", "reserved_room_type"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise CSVProcessingError(f"Отсутствуют обязательные колонки: {', '.join(missing)}.")


def clean_numeric_series(series: pd.Series, default, dtype) -> pd.Series:
    """
    Очистка числовой серии:
    — нормализует мусорные значения,
    — конвертирует в числа,
    — приводит к dtype.
    """
    s = series.astype(str).str.strip()
    bad_values = ["", "None", "none", "NULL", "null", "NaN", "nan", "N/A", "n/a"]

    s = s.replace(bad_values, str(default))
    s = s.replace(r"^\s*$", str(default), regex=True)

    numeric = pd.to_numeric(s, errors="coerce")
    numeric = numeric.fillna(default)

    return numeric.astype(dtype)


def normalize_columns(df: pd.DataFrame, config: dict, *, numeric: bool = False) -> pd.DataFrame:
    """
    Универсальная нормализация набора колонок по заданной конфигурации.

    Для каждой колонки:
    - создаёт колонку, если отсутствует;
    - заполняет пропуски значениями default;
    - приводит тип;
    - вызывает числовую очистку, если mode = numeric=True.
    """
    for col, cfg in config.items():
        default = cfg["default"]
        dtype = cfg["dtype"]

        if col not in df.columns:
            df[col] = pd.Series([default] * len(df), dtype=dtype)
            continue

        if numeric:
            df[col] = clean_numeric_series(df[col], default, dtype)
        else:
            df[col] = df[col].fillna(default).astype(dtype)

    return df


def compute_aggregates(df: pd.DataFrame, aggregates: dict) -> pd.DataFrame:
    """
    Вычисление агрегированных колонок.
    Если агрегируемая колонка уже существует и > 0 — сохраняет её.
    """
    df = df.copy()

    for target, parts in aggregates.items():
        # Сумма по всем нужным колонкам (если колонки нет — берём 0)
        sum_series = df[parts].sum(axis=1, min_count=1).fillna(0)

        if target in df.columns:
            # Только те строки, где агрегат ≤ 0, заменяем суммой
            mask = df[target] <= 0
            df.loc[mask, target] = sum_series[mask]
        else:
            df[target] = sum_series

    return df


def normalize_booking_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Последовательная нормализация данных бронирования."""
    df = df.copy()
    df = normalize_columns(df, CATEGORICAL_COLUMNS, numeric=False)
    df = normalize_columns(df, NUMERIC_COLUMNS, numeric=True)
    df = compute_aggregates(df, AGGREGATES)
    return df


# === Общий pipeline подготовки ===

async def prepare_booking_dataframe(
        content: str,
        hotel_id: int,
) -> pd.DataFrame:
    """
    Полная подготовка DataFrame:
    1. чтение CSV → DataFrame
    2. валидация;
    3. нормализация данных и заполнение пропусков;
    4. добавление колонки arrival_date_parsed
    5. извлечение существующих booking_ref из БД
    """
    logger.info("Начата обработка CSV для отеля %s (размер файла: %d байт)", hotel_id, len(content))

    if not content.strip():
        raise CSVProcessingError("Загруженный файл пуст.")

    # --- CPU-bound части переносим в thread pool ---
    df = await asyncio.to_thread(read_csv_to_dataframe, content)
    await asyncio.to_thread(validate_booking_columns, df)
    df = await asyncio.to_thread(normalize_booking_dataframe, df)
    df["arrival_date_parsed"] = await asyncio.to_thread(parse_dates_vectorized, df)

    logger.info("Подготовлено строк: %s", len(df))
    return df