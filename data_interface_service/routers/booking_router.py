import logging
from fastapi import APIRouter, File, UploadFile, Depends, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from data_interface_service.services.booking_service import import_bookings_from_csv, save_bookings_to_db
from data_interface_service.schemas import BookingImportResponse
from shared.db import get_async_session
from shared.models import Hotel
from data_interface_service.exceptions import ServiceError, AuthorizationError
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/import",
    response_model=BookingImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Импорт бронирований из CSV-файла.",
    response_description="Возвращает количество добавленных и пропущенных записей.",
    responses={
        201: {"description": "Файл успешно обработан, данные сохранены."},
        400: {"description": "Ошибка чтения или структуры CSV-файла."},
        401: {"description": "Неверный идентификатор отеля."},
        409: {"description": "Все записи уже существуют, новые не добавлены."},
        500: {"description": "Ошибка при сохранении данных в базу."},
    },
)
async def import_bookings(
    file: UploadFile = File(...),
    x_hotel_id: int = Header(...),
    db: AsyncSession = Depends(get_async_session)
) -> JSONResponse:
    """
    Загружает CSV-файл бронирований, валидирует и сохраняет записи в базу.
    """
    logger.info("Получен файл бронирований от hotel_id=%s: %s", x_hotel_id, file.filename)

    hotel = await db.get(Hotel, x_hotel_id)
    if not hotel:
        raise AuthorizationError()

    try:
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

    except ServiceError as e:
        logger.warning("Ошибка загрузки CSV (hotel_id=%s): %s", x_hotel_id, e.message)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"type": e.__class__.__name__, "message": e.message}}
        )

    logger.info(
        "Загрузка завершена успешно: hotel_id=%s, добавлено=%s, дубликатов=%s",
        x_hotel_id, added, duplicates_skipped
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=BookingImportResponse(
            hotel_id=x_hotel_id,
            added=added,
            duplicates_skipped=duplicates_skipped,
        ).model_dump(),
    )
