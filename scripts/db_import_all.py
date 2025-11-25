"""
Импорт CSV, праздников, погоды и демо-прогнозов.
Используется после базового seed.
"""

import asyncio
import logging
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db import AsyncSessionLocal

from data_import.import_bookings import load_bookings_from_csv, assign_booking_refs
from data_import.import_holidays import load_holidays_to_db
from data_import.import_weather import load_weather_data
from data_import.insert_prediction import insert_predictions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_data(session: AsyncSession) -> None:
    logger.info("Начало полного импорта данных...")

    # === Бронирования ====
    count = await load_bookings_from_csv("data_import/hotel_bookings.csv", session)
    await assign_booking_refs(session)
    logger.info(f"Импорт бронирований: {count}")

    # === Праздники ===
    count = await load_holidays_to_db(date(2015, 7, 1), date(2017, 8, 31), session)
    logger.info(f"Импорт праздников: {count}")

    # === Погода ====
    count = await load_weather_data(
        start=datetime(2015, 7, 1),
        end=datetime(2017, 8, 31),
        session=session,
    )
    logger.info(f"Импорт погоды: {count}")

    # === Демонстрационные прогнозы ===
    await insert_predictions(hotel_id=1, has_deposit=False, session=session)
    logger.info("Импорт демо-прогнозов завершён.")


async def main():
    async with AsyncSessionLocal() as session:
        await import_data(session)


if __name__ == "__main__":
    asyncio.run(main())
