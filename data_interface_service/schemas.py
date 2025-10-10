from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import date


class ForecastRequest(BaseModel):
    """Запрос на получение истории и прогноза бронирований."""
    target_date: date = Field(..., description="Целевая дата прогноза (YYYY-MM-DD)")
    horizon: int = Field(..., ge=1, le=30, description="Горизонт прогноза, дней")
    history_window: int = Field(30, ge=1, le=90, description="Окно истории, дней")
    has_deposit: bool = Field(..., description="True — с депозитом, False — без")


class ForecastDay(BaseModel):
    """День истории или прогноза."""
    date: date = Field(..., description="Дата (YYYY-MM-DD)")
    bookings: float = Field(..., ge=0, description="Все бронирования")
    cancellations: float = Field(..., ge=0, description="Отменённые бронирования")


class ForecastResponse(BaseModel):
    """Ответ с сохранённым прогнозом и историей из БД."""
    hotel_id: int = Field(..., description="Идентификатор отеля")
    history_summary: List[ForecastDay] = Field(...,description="История бронирований")
    forecast: List[ForecastDay] = Field(..., description="Прогноз бронирований")


class BookingImportResponse(BaseModel):
    """Результат загрузки файла бронирований."""
    hotel_id: int = Field(..., description="Идентификатор отеля, отправившего данные")
    added: Optional[int] = Field(None, ge=0, description="Количество добавленных записей")
    duplicates_skipped: Optional[int] = Field(None, ge=0, description="Количество пропущенных дубликатов")