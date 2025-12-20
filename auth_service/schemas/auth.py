from pydantic import BaseModel, Field, ConfigDict

from auth_service.schemas.roles import SystemRole
from auth_service.schemas.token import HotelAccessPayload


class AuthPrincipal(BaseModel):
    user_id: int = Field(..., gt=0)

    ConfigDict(frozen=True)


class HotelPrincipal(BaseModel):
    user_id: int
    system_role: SystemRole
    hotels: list[HotelAccessPayload]

    model_config = ConfigDict(frozen=True)
