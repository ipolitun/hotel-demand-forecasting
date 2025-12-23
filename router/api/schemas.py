from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr


# === AUTH ===
class UserLoginRequest(BaseModel):
    """Запрос на вход пользователя по email и паролю."""
    email: EmailStr = Field(..., description="Email пользователя.")
    password: str = Field(..., max_length=32, description="Пароль пользователя.", min_length=8)


class PasswordUpdateRequest(BaseModel):
    """Запрос на смену пароля пользователя."""
    current_password: str = Field(..., min_length=8, max_length=32, description="Текущий пароль пользователя.")
    new_password: str = Field(..., min_length=8, max_length=32, description="Новый пароль пользователя.")


class UserRegisterRequest(BaseModel):
    """ Запрос на регистрацию нового пользователя."""
    email: EmailStr = Field(..., description="Уникальный Email пользователя")
    password: str = Field(..., min_length=8, max_length=32, description="Пароль пользователя.")
    name: str = Field(..., description="Имя пользователя.")
    surname: str = Field(..., description="Фамилия пользователя.")


class UserRegisterResponse(BaseModel):
    """Ответ с данными зарегистрированного пользователя."""
    id: int = Field(..., description="Уникальный идентификатор пользователя в системе.")
    email: EmailStr = Field(..., description="Email пользователя.")
    name: str = Field(..., description="Имя пользователя.")
    surname: str = Field(..., description="Фамилия пользователя.")
    is_active: bool = Field(..., description="Флаг активности пользователя.")


# === DATA INTERFACE (загрузка бронирований и чтение сохранённых прогнозов) ===
class HotelUserRole(str, Enum):
    """Роль пользователя в отеле"""
    owner = "owner"
    manager = "manager"
    viewer = "viewer"


class AccessibleHotel(BaseModel):
    """Отель, доступный пользователю согласно access-токену"""
    id: int = Field(..., description="Идентификатор отеля, к которому пользователь имеет доступ.")
    user_role: HotelUserRole = Field(..., description="Роль пользователя в данном отеле.")


class ForecastRequest(BaseModel):
    """Запрос на получение истории и прогноза бронирований"""
    target_date: date = Field(..., description="Целевая дата прогноза (YYYY-MM-DD)")
    horizon: int = Field(..., ge=0, le=30, description="Горизонт прогноза, дней")
    history_window: int = Field(30, ge=1, le=90, description="Окно истории, дней")
    has_deposit: bool = Field(..., description="True — с депозитом, False — без")


class ForecastDay(BaseModel):
    """День истории или прогноза"""
    day: date = Field(..., description="Дата (YYYY-MM-DD)")
    bookings: float = Field(..., ge=0, description="Все бронирования")
    cancellations: float = Field(..., ge=0, description="Отменённые бронирования")


class ForecastResponse(BaseModel):
    """Ответ с сохранённым прогнозом и историей из БД"""
    hotel_id: int = Field(..., description="Идентификатор отеля")
    history_summary: List[ForecastDay] = Field(..., description="История бронирований за выбранный период")
    forecast: List[ForecastDay] = Field(..., description="Прогноз бронирований на заданный горизонт")


class BookingImportResponse(BaseModel):
    """Результат загрузки файла бронирований"""
    hotel_id: int = Field(..., description="Идентификатор отеля, отправившего данные")
    added: Optional[int] = Field(None, ge=0, description="Количество добавленных записей")
    duplicates_skipped: Optional[int] = Field(None, ge=0, description="Количество пропущенных дубликатов")


# === PREDICTION (генерация прогноза моделью) ===
class PredictRequest(BaseModel):
    """Запрос на генерацию прогноза с использованием модели"""
    hotel_id: int = Field(..., description="Идентификатор отеля")
    target_date: date = Field(..., description="Целевая дата прогноза (YYYY-MM-DD)")
    has_deposit: bool = Field(..., description="True — с депозитом, False — без")


class PredictDay(BaseModel):
    """День прогноза (результаты модели)"""
    day: date = Field(..., description="Дата прогноза (YYYY-MM-DD)")
    bookings: float = Field(..., ge=0, description="Количество всех бронирований")
    cancellations: float = Field(..., ge=0, description="Количество отменённых бронирований")


class PredictResponse(BaseModel):
    """Ответ на запрос прогноза модели"""
    hotel_id: int = Field(..., description="Идентификатор отеля")
    target_date: date = Field(..., description="Целевая дата прогноза (YYYY-MM-DD)")
    forecast: List[PredictDay] = Field(..., description="Список дней с прогнозами бронирований")
