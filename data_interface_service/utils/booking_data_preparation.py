from io import StringIO
from datetime import date
import logging
from typing import Tuple, Set

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Booking
from data_interface_service.exceptions import CSVProcessingError

logger = logging.getLogger(__name__)

MONTH_MAP = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}

NUMERIC_GROUPS = {
    "guests": {"cols": ["adults", "children", "babies", "total_guests"], "default": 0, "type": int},
    "nights": {"cols": ["stays_in_weekend_nights", "stays_in_week_nights", "total_nights"], "default": 0, "type": int},
    "metrics": {"cols": ["lead_time", "booking_changes", "adr"], "default": 0.0, "type": float},
}

# --- CSV: чтение и подготовка ---

def detect_separator(content: str) -> str:
    """Определяет разделитель CSV-файла."""
    sample = content[:1000]
    sep = ';' if sample.count(';') > sample.count(',') else ','
    logger.debug("Определён разделитель CSV: '%s'", sep)
    return sep


def read_csv_to_dataframe(content: str) -> pd.DataFrame:
    """Читает CSV в DataFrame с автоопределением разделителя."""
    try:
        sep = detect_separator(content)
        df = pd.read_csv(StringIO(content), sep=sep)
    except Exception as e:
        logger.exception("Ошибка чтения CSV: %s", e)
        raise CSVProcessingError("Ошибка чтения CSV (неверный формат или разделитель).")

    if df.empty:
        raise CSVProcessingError("Файл пуст.")

    logger.debug("CSV успешно прочитан: %s строк, %s колонок", df.shape[0], df.shape[1])
    return df

# --- Валидация и нормализация ---

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


def normalize_booking_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Заполняет отсутствующие поля и пропуски по умолчанию."""
    df['market_segment'] = df.get('market_segment', 'Undefined')
    df['distribution_channel'] = df.get('distribution_channel', 'Undefined')
    df["booking_ref"] = df.get("booking_ref", pd.Series(dtype=str)).fillna("")

    for group_name, group in NUMERIC_GROUPS.items():
        for col in group["cols"]:
            default = group["default"]
            dtype = group["type"]
            df[col] = df.get(col, default).fillna(default).astype(dtype)

    return df


def parse_date(row) -> date:
    """
    Формирует дату прибытия:
    - либо из строки arrival_date (формат DD.MM.YYYY),
    - либо из частей: arrival_date_year, arrival_date_month, arrival_date_day_of_month.
    """
    try:
        if "arrival_date" in row and pd.notna(row["arrival_date"]):
            return pd.to_datetime(row["arrival_date"], format="%d.%m.%Y").date()

        return date(
            int(row["arrival_date_year"]),
            MONTH_MAP[row["arrival_date_month"]],
            int(row["arrival_date_day_of_month"]),
        )

    except ValueError as e:
        raise CSVProcessingError(
            f"Некорректный формат даты. Ожидается 'ДД.ММ.ГГГГ', получено: {row.get('arrival_date', 'N/A')}"
        )

    except Exception as e:
        logger.error("Ошибка формирования даты прибытия: %s", e)
        raise CSVProcessingError("Ошибка формирования даты прибытия. Проверьте поля arrival_date или year/month/day")

# --- Работа с БД ---

async def get_existing_booking_refs(db: AsyncSession, hotel_id: int) -> Set[str]:
    """Извлекает существующие booking_ref из базы (для исключения дубликатов)."""
    stmt = (
        select(Booking.booking_ref)
        .where(Booking.hotel_id == hotel_id)
        .where(Booking.booking_ref.isnot(None))
    )
    result = await db.execute(stmt)
    refs = {ref for (ref,) in result.all()}
    logger.debug("Hotel %s: найдено %s существующих booking_ref", hotel_id, len(refs))
    return refs

# --- Общий pipeline подготовки ---

async def prepare_booking_dataframe(
        content: str,
        hotel_id: int,
        db: AsyncSession,
) -> Tuple[pd.DataFrame, Set[str]]:
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

    df = read_csv_to_dataframe(content)
    validate_booking_columns(df)
    df = normalize_booking_dataframe(df)
    df["arrival_date_parsed"] = df.apply(parse_date, axis=1)

    existing_refs = await get_existing_booking_refs(db, hotel_id)
    logger.info("Подготовлено строк: %s; существующих booking_ref: %s", len(df), len(existing_refs))
    return df, existing_refs