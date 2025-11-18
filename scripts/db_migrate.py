"""
Скрипт для миграции БД: добавляет колонку booking_ref и заполняет её.

Используется вручную при изменении схемы.
"""

import logging
from sqlalchemy import text
from shared.db_models import Booking
from shared.db import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """
    Добавляет колонку booking_ref в таблицу booking и назначает значения по порядку.
    """

    with SessionLocal() as session:
        try:
            session.execute(text("ALTER TABLE booking ADD COLUMN booking_ref VARCHAR"))
            session.commit()
            logger.info("Колонка booking_ref добавлена")
        except Exception as e:
            session.rollback()
            logger.warning(f"Колонка booking_ref уже существует или возникла ошибка: {e}")

        hotel_ids = session.query(Booking.hotel_id).distinct().all()

        for (hotel_id,) in hotel_ids:
            bookings = (
                session.query(Booking)
                .filter(Booking.hotel_id == hotel_id)
                .order_by(Booking.id)
                .all()
            )
            for idx, booking in enumerate(bookings, start=1):
                booking.booking_ref = str(idx)

        session.commit()
        logger.info("Значения booking_ref присвоены")


if __name__ == "__main__":
    migrate()
