from datetime import date, timedelta
import logging

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from data_interface_service.schemas import ForecastDay
from data_interface_service.utils.mapping import map_to_forecast_day
from shared.db_models import Booking, Prediction
from shared.errors import (
    InsufficientHistoryError,
    NoForecastError,
)

logger = logging.getLogger(__name__)


async def get_history(
    db: AsyncSession,
    hotel_id: int,
    target_date: date,
    has_deposit: bool,
    history_window: int = 30,
) -> list[ForecastDay]:
    """
    Достаёт историю бронирований и отмен за окно window_days до target_date.
    Возвращает список объектов ForecastDay.
    """

    start_date = target_date - timedelta(days=history_window)

    conditions = [
        Booking.hotel_id == hotel_id,
        Booking.arrival_date >= start_date,
        Booking.arrival_date <= target_date,
        Booking.has_deposit == has_deposit,
    ]

    bookings_sum = func.count(Booking.id)
    cancellations_sum = func.sum(case((Booking.is_cancellation == True, 1), else_=0))

    stmt = (
        select(
            Booking.arrival_date.label("arrival_date"),
            bookings_sum.label("bookings"),
            cancellations_sum.label("cancellations"),
        )
        .where(and_(*conditions))
        .group_by(Booking.arrival_date)
        .order_by(Booking.arrival_date.asc())
    )

    result = await db.execute(stmt)
    history_records = result.all()

    if not history_records:
        logger.warning("История пуста", extra={"hotel_id": hotel_id, "target_date": target_date})
        raise InsufficientHistoryError(
            f"Недостаточно данных для прогноза за {history_window} дней до {target_date}."
        )

    history_days = [map_to_forecast_day(record, "arrival_date") for record in history_records]

    total_bookings = sum(day.bookings for day in history_days)
    if total_bookings < 30:
        logger.warning(
            "Недостаточно данных для прогноза (история)",
            extra={"hotel_id": hotel_id, "target_date": target_date, "bookings": total_bookings},
        )
        raise InsufficientHistoryError(
            f"Недостаточно данных для прогноза: всего {total_bookings} бронирований."
        )

    return history_days


async def get_forecast(
    db: AsyncSession,
    hotel_id: int,
    target_date: date,
    has_deposit: bool,
    horizon: int = 30,
) -> list[ForecastDay]:
    """
    Возвращает прогноз бронирований из Prediction на horizon дней начиная с target_date.
    """
    forecast_start = target_date
    forecast_end = target_date + timedelta(days=horizon - 1)

    conditions = [
        Prediction.hotel_id == hotel_id,
        Prediction.target_date >= forecast_start,
        Prediction.target_date <= forecast_end,
        Prediction.has_deposit == has_deposit,
    ]

    stmt = (
        select(Prediction)
        .where(and_(*conditions))
        .order_by(Prediction.target_date.asc())
    )

    result = await db.execute(stmt)
    forecast_records = result.scalars().all()

    if not forecast_records:
        logger.warning("Прогноз пуст", extra={"hotel_id": hotel_id, "target_date": target_date})
        raise NoForecastError(
            f"Прогноз отсутствует для периода {target_date} — {forecast_end}."
        )

    forecast_days = [map_to_forecast_day(r, "target_date") for r in forecast_records]

    return forecast_days

