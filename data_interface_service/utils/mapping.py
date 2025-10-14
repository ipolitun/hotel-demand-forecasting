import logging
from data_interface_service.schemas import ForecastDay
from shared.models import Booking
from shared.errors import MappingError

logger = logging.getLogger(__name__)


def map_row_to_booking(row, hotel_id: int) -> Booking | None:
    """
    Преобразует строку DataFrame в объект Booking.
    """
    try:
        # Расчёт производных признаков
        total_guests = int(row.get("total_guests") or (row["adults"] + row["children"] + row["babies"]))
        total_nights = int(row.get("total_nights") or (row["stays_in_weekend_nights"] + row["stays_in_week_nights"]))

        if total_guests <= 0 or total_nights <= 0:
            return None # Пропускаем записи без гостей или с нулевыми ночами

        return Booking(
            hotel_id=hotel_id,
            booking_ref=str(row["booking_ref"]).strip() or None,
            arrival_date=row["arrival_date_parsed"],
            lead_time=int(row["lead_time"]),
            adr=float(row["adr"]),
            total_guests=total_guests,
            total_nights=total_nights,
            booking_changes=int(row["booking_changes"]),
            has_deposit=str(row["has_deposit"]).lower() != "no deposit",
            is_cancellation=bool(row["is_cancellation"]),
            market_segment=row["market_segment"],
            distribution_channel=row["distribution_channel"],
            reserved_room_type=row["reserved_room_type"],
            day_of_week=row["arrival_date_parsed"].weekday()
        )
    except (ValueError, TypeError) as e:
        logger.error("Некорректный тип данных при маппинге строки: %s", e)
        raise MappingError(f"Некорректные значения в строке CSV: {e}")

    except Exception as e:
        logger.exception("Неожиданная ошибка при формировании Booking: %s", e)
        raise MappingError(f"Ошибка при формировании объекта Booking: {e}")


def map_to_forecast_day(record, date_field: str = "arrival_date") -> ForecastDay:
    """
    Преобразует объект ORM или строку результата SQLAlchemy в ForecastDay.
    """
    dt = getattr(record, date_field, None)
    if dt is None:
        raise MappingError(f"Record не содержит поля {date_field}")

    return ForecastDay(
        date=dt,
        bookings=float(getattr(record, "bookings", 0) or 0),
        cancellations=float(getattr(record, "cancellations", 0) or 0),
    )
