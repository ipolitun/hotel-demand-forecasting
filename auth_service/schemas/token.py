from enum import Enum

from pydantic import BaseModel

from auth_service.schemas.roles import SystemRole
from auth_service.schemas.hotel import HotelAccessPayload


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenBase(BaseModel):
    sub: str
    exp: int | None = None
    token_type: TokenType


class TokenAccessPayload(TokenBase):
    system_role: SystemRole | None = None
    hotels: list[HotelAccessPayload] | None = None


class TokenRefreshPayload(TokenBase):
    jti: str | None = None

