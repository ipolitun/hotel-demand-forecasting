"""
Скрипт для подсчёта бронирований и отмен за заданный период.
Используется для отладки и проверки БД.
"""

import logging
from datetime import date, timedelta

from shared.db import SessionLocal
from shared.db_models import Booking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def counter():
    """
    Считает количество бронирований и отмен для заданного отеля и диапазона дат.
    """
    hotel_id = 1
    has_deposit = False
    start_date = date(2017, 6, 8)
    horizon = 30

    with SessionLocal() as session:
        for offset in range(horizon):
            current_date = start_date + timedelta(days=offset)

            bookings = session.query(Booking).filter(
                Booking.hotel_id == hotel_id,
                Booking.arrival_date == current_date,
                Booking.has_deposit == has_deposit,
                Booking.is_cancellation.is_(False)
            ).count()

            cancellations = session.query(Booking).filter(
                Booking.hotel_id == hotel_id,
                Booking.arrival_date == current_date,
                Booking.has_deposit == has_deposit,
                Booking.is_cancellation.is_(True)
            ).count()

            logger.info(
                f"{current_date}: бронирования={bookings}, отмены={cancellations}"
            )


if __name__ == "__main__":
    counter()
