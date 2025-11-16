"""
Импорт данных о бронированиях из CSV в базу данных.
Используется для первичного наполнения таблицы Booking.
"""

import pandas as pd
from datetime import date
from sqlalchemy.orm import Session

from shared.models import Booking, Hotel
from shared.db import SessionLocal


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


def load_bookings_from_csv(csv_path: str, db: Session) -> int:
    """Загружает бронирования из CSV в таблицу Booking."""
    df = pd.read_csv(csv_path)
    df = preprocess_dataframe(df)

    hotels = {h.name: h for h in db.query(Hotel).all()}

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
            )
        )

    db.add_all(bookings)
    db.commit()
    return len(bookings)


def main() -> None:
    """Точка входа: загрузка CSV-файла бронирований в БД."""
    csv_path = "data_import/hotel_bookings.csv"
    with SessionLocal() as session:
        count = load_bookings_from_csv(csv_path, session)
        print(f"Загружено {count} записей из {csv_path}")


if __name__ == "__main__":
    main()
