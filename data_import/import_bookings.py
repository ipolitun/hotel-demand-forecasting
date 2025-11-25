"""
Импорт данных о бронированиях из CSV в базу данных.
Используется для первичного наполнения таблицы Booking.
"""
import asyncio

import pandas as pd
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import Booking, Hotel
from shared.db import AsyncSessionLocal


def make_date(record: pd.Series) -> date:
    """Формирует дату заезда из отдельных компонент CSV."""
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12,
    }
    return date(
        int(record["arrival_date_year"]),
        month_map[record["arrival_date_month"]],
        int(record["arrival_date_day_of_month"]),
    )


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Очищает и подготавливает датафрейм к загрузке."""
    df = df.copy()
    df["market_segment"] = df["market_segment"].fillna("Undefined")
    df["distribution_channel"] = df["distribution_channel"].fillna("Undefined")

    numeric_columns = [
        "adults", "children", "babies",
        "stays_in_weekend_nights", "stays_in_week_nights",
        "lead_time", "booking_changes", "adr",
    ]
    df[numeric_columns] = df[numeric_columns].fillna(0)
    return df


async def load_bookings_from_csv(csv_path: str, session: AsyncSession) -> int:
    """Загружает бронирования из CSV в таблицу Booking."""
    df = pd.read_csv(csv_path)
    df = preprocess_dataframe(df)

    # === Асинхронная загрузка отелей ===
    result = await session.execute(select(Hotel))
    hotels = {h.name: h for h in result.scalars().all()}

    bookings: list[Booking] = []

    for _, row in df.iterrows():
        # Пропускаем пустые или некорректные записи
        if row["adults"] + row["children"] + row["babies"] == 0:
            continue
        if row["stays_in_weekend_nights"] + row["stays_in_week_nights"] == 0:
            continue

        arrival = make_date(row)
        total_guests = int(row["adults"] + row["children"] + row["babies"])
        total_nights = int(row["stays_in_weekend_nights"] + row["stays_in_week_nights"])

        hotel_name = "Hotel A" if row["hotel"] == "City Hotel" else "Hotel B"
        hotel = hotels.get(hotel_name)
        if not hotel:
            continue

        bookings.append(
            Booking(
                hotel_id=hotel.id,
                arrival_date=arrival,
                lead_time=int(row["lead_time"]),
                adr=float(row["adr"]),
                total_guests=total_guests,
                total_nights=total_nights,
                booking_changes=int(row["booking_changes"]),
                has_deposit=row["deposit_type"] != "No Deposit",
                is_cancellation=bool(row["is_canceled"]),
                market_segment=row["market_segment"],
                distribution_channel=row["distribution_channel"],
                reserved_room_type=row["reserved_room_type"],
                day_of_week=arrival.weekday(),
                # booking_ref будет сгенерирован позже
            )
        )

    session.add_all(bookings)
    await session.commit()
    return len(bookings)


async def assign_booking_refs(session: AsyncSession) -> None:
    """Генерирует booking_ref для каждой группы записей по hotel_id."""
    result = await session.execute(select(Hotel.id))
    hotel_ids = result.scalars().all()

    for hotel_id in hotel_ids:
        res = await session.execute(
            select(Booking)
            .where(Booking.hotel_id == hotel_id)
            .order_by(Booking.id)
        )
        rows = res.scalars().all()

        for idx, booking in enumerate(rows, start=2):
            booking.booking_ref = str(idx)

    await session.commit()


async def main() -> None:
    """Точка входа: загрузка CSV-файла бронирований в БД."""
    csv_path = "data_import/hotel_bookings.csv"
    async with AsyncSessionLocal() as session:
        count = await load_bookings_from_csv(csv_path, session)
        await assign_booking_refs(session)
        print(f"Загружено {count} записей из {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
