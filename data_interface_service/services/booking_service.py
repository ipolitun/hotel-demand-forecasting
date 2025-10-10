import logging
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.utils.booking_data_preparation import prepare_booking_dataframe
from data_interface_service.utils.mapping import map_row_to_booking
from data_interface_service.exceptions import (
    CSVProcessingError,
    MappingError,
    DatabaseError,
    ConflictError,
)
from shared.models import Booking

logger = logging.getLogger(__name__)


async def import_bookings_from_csv(
    db: AsyncSession,
    hotel_id: int,
    content: str,
) -> Tuple[List[Booking], int]:
    """
    Обработка CSV:
    - подготовка DataFrame (чтение, валидация, нормализация, парсинг дат),
    - исключение дубликатов по booking_ref,
    - маппинг строк → ORM Booking.
    """
    logger.info("Начата обработка CSV для отеля %s", hotel_id)

    df, existing_refs = await prepare_booking_dataframe(content, hotel_id, db)

    bookings: List[Booking] = []
    duplicates_skipped = 0

    for row in df.itertuples(index=False):
        booking_ref = str(getattr(row, "booking_ref", "")).strip()

        if booking_ref and booking_ref in existing_refs:
            duplicates_skipped += 1
            continue

        try:
            booking = map_row_to_booking(row._asdict(), hotel_id)
            if booking:
                bookings.append(booking)
        except MappingError as e:
            logger.error("Ошибка маппинга в строке %s (booking_ref=%s): %s", booking_ref, e)
            raise

    if not bookings and duplicates_skipped > 0:
        raise ConflictError("Все записи уже существуют, новые бронирования не добавлены.")

    if not bookings and duplicates_skipped == 0:
        raise CSVProcessingError("Не удалось добавить ни одной записи. Проверьте CSV.")

    logger.info(
        "Hotel %s: добавлено %s записей, пропущено %s дубликатов.",
        hotel_id, len(bookings), duplicates_skipped
    )
    return bookings, duplicates_skipped


async def save_bookings_to_db(
    db: AsyncSession,
    bookings: list[Booking],
) -> int:
    """
    Сохраняет бронирования в БД.
    """
    try:
        db.add_all(bookings)
        await db.commit()
        logger.info("Сохранено %s бронирований в БД", len(bookings))
        return len(bookings)

    except Exception as e:
        await db.rollback()
        logger.exception("Ошибка при сохранении данных в БД: %s", e)
        raise DatabaseError("Ошибка при сохранении данных в базу.")
