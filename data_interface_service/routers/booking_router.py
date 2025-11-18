import logging
from fastapi import APIRouter, File, UploadFile, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.services.booking_service import import_bookings_from_csv, save_bookings_to_db
from data_interface_service.schemas import BookingImportResponse
from shared.db import get_async_session
from shared.db_models import Hotel
from shared.errors import (
    register_errors,
    AuthorizationError,
    CSVProcessingError,
    ConflictError,
    DatabaseError,
    MappingError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/import",
    response_model=BookingImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Импорт бронирований из CSV-файла",
    response_description="Возвращает количество добавленных и пропущенных записей",
)
@register_errors(
    AuthorizationError, MappingError,
    CSVProcessingError, ConflictError, DatabaseError
)
async def import_bookings(
    file: UploadFile = File(...),
    x_hotel_id: int = Header(...),
    db: AsyncSession = Depends(get_async_session)
) -> BookingImportResponse:
    """
    Загружает CSV-файл бронирований, валидирует и сохраняет записи в базу.
    """
    logger.info("Получен файл бронирований от hotel_id=%s: %s", x_hotel_id, file.filename)

    hotel = await db.get(Hotel, x_hotel_id)
    if not hotel:
        raise AuthorizationError()

    content = (await file.read()).decode("utf-8")
    bookings, duplicates_skipped = await import_bookings_from_csv(
        content=content,
        hotel_id=hotel.id,
        db=db
    )
    added = await save_bookings_to_db(
        db=db,
        bookings=bookings
    )

    logger.info(
        "Импорт завершён: hotel_id=%s, добавлено=%s, дубликатов=%s",
        x_hotel_id, added, duplicates_skipped
    )

    return BookingImportResponse(
        hotel_id=x_hotel_id,
        added=added,
        duplicates_skipped=duplicates_skipped,
    )
