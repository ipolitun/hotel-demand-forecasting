from sqlalchemy import Numeric, ForeignKey, text, Enum as SqlEnum, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date

from shared.db import Base
from shared.enums import UserRole, SystemRole


class City(Base):
    __tablename__ = "city"

    name: Mapped[str] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    region: Mapped[str | None]

    hotels: Mapped[list["Hotel"]] = relationship(back_populates="city")
    weather: Mapped[list["Weather"]] = relationship(back_populates="city")


class User(Base):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    system_role: Mapped[SystemRole] = mapped_column(
        SqlEnum(SystemRole, name="system_role"),
        nullable=False,
        server_default=SystemRole.user.value,
    )

    hotels: Mapped[list["UserHotel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserHotel(Base):
    __tablename__ = "user_hotel"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotel.id"), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        nullable=False,
        server_default=UserRole.viewer.value
    )

    user: Mapped["User"] = relationship(back_populates="hotels")
    hotel: Mapped["Hotel"] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "hotel_id", name="uq_user_hotel"),
    )


class Hotel(Base):
    __tablename__ = "hotel"

    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"), nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)
    is_city_hotel: Mapped[bool] = mapped_column(nullable=False)
    api_key: Mapped[str] = mapped_column(unique=True, nullable=False)

    city: Mapped["City"] = relationship(back_populates="hotels")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="hotel", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="hotel", cascade="all, delete-orphan"
    )
    users: Mapped[list["UserHotel"]] = relationship(
        back_populates="hotel",
        cascade="all, delete-orphan"
    )


class Booking(Base):
    __tablename__ = "booking"

    booking_ref: Mapped[str | None]
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotel.id"), nullable=False)

    arrival_date: Mapped[date] = mapped_column(nullable=False)
    lead_time: Mapped[int | None]
    adr: Mapped[float | None]
    total_guests: Mapped[int | None]
    total_nights: Mapped[int | None]
    booking_changes: Mapped[int | None]
    has_deposit: Mapped[bool | None]
    is_cancellation: Mapped[bool | None]

    market_segment: Mapped[str | None]
    distribution_channel: Mapped[str | None]
    reserved_room_type: Mapped[str | None]
    day_of_week: Mapped[int | None]

    hotel: Mapped["Hotel"] = relationship(back_populates="bookings")


class Weather(Base):
    __tablename__ = "weather"

    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"), nullable=False)

    day: Mapped[date] = mapped_column(nullable=False)
    temp_avg: Mapped[float | None]  # Среднесуточная температура
    precipitation: Mapped[float | None]
    wind_speed: Mapped[float | None]
    weather_desc: Mapped[str | None]

    city: Mapped["City"] = relationship(back_populates="weather")


class Holiday(Base):
    __tablename__ = "holiday"

    day: Mapped[date] = mapped_column(nullable=False, unique=True)
    holiday_name: Mapped[str] = mapped_column(nullable=False)
    is_national: Mapped[bool] = mapped_column(default=True, server_default=text("'true'"))
    region: Mapped[str | None]


class Prediction(Base):
    __tablename__ = "prediction"

    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotel.id"), nullable=False)

    target_date: Mapped[date] = mapped_column(nullable=False)
    has_deposit: Mapped[bool | None]

    bookings: Mapped[float | None]
    cancellations: Mapped[float | None]

    hotel: Mapped["Hotel"] = relationship(back_populates="predictions")
