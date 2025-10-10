import secrets

from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.db import get_sync_session
from shared.models import Hotel

def create_hotel(name: str, is_city_hotel: bool, db: Session) -> str:
    """
    Создание отеля и генерация API-ключа.
    """
    api_key = secrets.token_hex(16)
    hotel = Hotel(name=name, is_city_hotel=is_city_hotel, api_key=api_key)
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel


def get_hotel_by_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_sync_session)
) -> Hotel:
    hotel = db.query(Hotel).filter(Hotel.api_key == x_api_key).first()
    if not hotel:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return hotel
