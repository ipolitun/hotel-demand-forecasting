from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


# === AUTH ===
class AuthRequest(BaseModel):
    """Запрос авторизации по API-ключу"""
    api_key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


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


# === DATA INTERFACE (загрузка бронирований и чтение сохранённых прогнозов) ===
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
