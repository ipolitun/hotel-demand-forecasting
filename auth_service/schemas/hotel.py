from pydantic import BaseModel, ConfigDict

from auth_service.schemas.roles import UserRole


class HotelBase(BaseModel):
    name: str
    is_city_hotel: bool


class HotelCreate(HotelBase):
    pass


class HotelShow(HotelBase):
    id: int
    api_key: str

    model_config = ConfigDict(from_attributes=True)


class HotelAccessPayload(BaseModel):
    id: int
    user_role: UserRole
