import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.utils.booking_data_preparation import prepare_booking_dataframe
from data_interface_service.utils.mapping import map_row_to_booking
from shared.db_models import Booking
from shared.errors import (
    CSVProcessingError,
    MappingError,
    DatabaseError,
    ConflictError,
)

logger = logging.getLogger(__name__)


async def import_bookings_from_csv(
    db: AsyncSession,
    hotel_id: int,
    content: str,
) -> tuple[list[dict], int]:
    """
    Обработка CSV:
    - подготовка DataFrame (чтение, валидация, нормализация, парсинг дат),
    - исключение дубликатов по booking_ref,
    - возвращает список бронирований и кол-во дубликатов
    """
    logger.info("Начата обработка CSV для отеля %s", hotel_id)

    df = await prepare_booking_dataframe(content, hotel_id)
    existing_refs = await get_existing_booking_refs(db, hotel_id)

    records = df.to_dict(orient="records")

    bookings: list[dict] = []
    duplicates_skipped = 0

    for row in records:
        booking_ref = str(row.get("booking_ref", "")).strip()

        if booking_ref and booking_ref in existing_refs:
            duplicates_skipped += 1
            continue
        bookings.append(row)

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
    bookings_data: list[dict],
    hotel_id: int,
) -> int:
    """
    Сохраняет бронирования в БД.
    """
    bookings: list[Booking] = []

    for row in bookings_data:
        try:
            booking = map_row_to_booking(row, hotel_id)
            if booking:
                bookings.append(booking)
        except MappingError as e:
            logger.error("Ошибка маппинга строки (booking_ref=%s): %s", row.get("booking_ref"), e)
            raise

    if not bookings:
        return 0

    try:
        db.add_all(bookings)
        await db.commit()
        logger.info("Сохранено %s бронирований в БД", len(bookings))
        return len(bookings)

    except Exception as e:
        await db.rollback()
        logger.exception("Ошибка при сохранении данных в БД: %s", e)
        raise DatabaseError("Ошибка при сохранении данных в базу.")


async def get_existing_booking_refs(db: AsyncSession, hotel_id: int) -> set[str]:
    """Извлекает существующие booking_ref из базы (для исключения дубликатов)."""
    stmt = (
        select(Booking.booking_ref)
        .where(Booking.hotel_id == hotel_id)
        .where(Booking.booking_ref.isnot(None))
    )
    result = await db.execute(stmt)
    refs = set(result.scalars().all())
    logger.debug("Hotel %s: найдено %s существующих booking_ref", hotel_id, len(refs))
    return refs