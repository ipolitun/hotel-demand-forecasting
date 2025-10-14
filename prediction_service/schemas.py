from datetime import date
from pydantic import BaseModel
from typing import List

class TrainRequest(BaseModel):
    hotel_id: int
    epochs: int = 10
    batch_size: int = 32
    init: bool = False


class TrainResponse(BaseModel):
    hotel_id: int
    message: str


class InitHotelRequest(BaseModel):
    hotel_id: int


class InitHotelResponse(BaseModel):
    hotel_id: int
    path: str


class ModelStatusResponse(BaseModel):
    hotel_id: int
    model_exists: bool
    config_exists: bool


class ModelConfigResponse(BaseModel):
    hotel_id: int
    config: dict


class PredictRequest(BaseModel):
    hotel_id: int
    target_date: date
    has_deposit: bool


class PredictDay(BaseModel):
    date: str
    bookings: float
    cancellations: float

    class Config:
        orm_mode = True


class PredictResponse(BaseModel):
    hotel_id: int
    target_date: date
    forecast: List[PredictDay]