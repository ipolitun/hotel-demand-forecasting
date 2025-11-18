import pandas as pd
from sqlalchemy.orm import Session
from shared.db_models import Booking, Weather, Holiday, Hotel
from shared.errors import DatabaseError, ValidationError


def load_bookings(hotel_id: int, db: Session) -> pd.DataFrame:
    """Загружает данные о бронированиях для указанного отеля."""
    try:
        records = db.query(Booking).filter(Booking.hotel_id == hotel_id).all()
    except Exception as e:
        raise DatabaseError(f"Ошибка при загрузке бронирований для hotel_id={hotel_id}: {e}")

    if not records:
        raise ValidationError(f"Нет данных о бронированиях для hotel_id={hotel_id}")

    df = pd.DataFrame([b.__dict__ for b in records])
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    return df


def load_weather(hotel_id: int, db: Session) -> pd.DataFrame:
    """Загружает погодные данные по городу, связанному с отелем."""
    try:
        city_id = db.query(Hotel.city_id).filter(Hotel.id == hotel_id).scalar()
    except Exception as e:
        raise DatabaseError(f"Ошибка при получении city_id для hotel_id={hotel_id}: {e}")

    if city_id is None:
        raise ValidationError(f"Не найден city_id для hotel_id={hotel_id}")

    try:
        records = db.query(Weather.day, Weather.temp_avg).filter(Weather.city_id == city_id).all()
    except Exception as e:
        raise DatabaseError(f"Ошибка при загрузке погодных данных для city_id={city_id}: {e}")

    df = pd.DataFrame(records, columns=["day", "temp_avg"])

    if df.empty:
        raise ValidationError(f"Нет погодных данных для city_id={city_id}")

    df["day"] = pd.to_datetime(df["day"], errors="coerce")
    df["temp_avg"] = pd.to_numeric(df["temp_avg"], errors="coerce")
    return df


def load_holidays(db: Session) -> pd.DataFrame:
    """Загружает данные о праздничных днях."""
    try:
        records = db.query(Holiday).all()
    except Exception as e:
        raise DatabaseError(f"Ошибка при загрузке данных о праздниках: {e}")

    if not records:
        raise ValidationError("Данные о праздничных днях отсутствуют")

    df = pd.DataFrame([h.__dict__ for h in records])
    df["day"] = pd.to_datetime(df["day"], errors="coerce")
    return df
