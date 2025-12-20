from pydantic import BaseModel, EmailStr, Field, ConfigDict

from auth_service.schemas.roles import UserRole


class UserBase(BaseModel):
    name: str
    surname: str
    email: EmailStr


class UserCredentials(BaseModel):
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class PasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class UserShow(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserHotelShow(BaseModel):
    user_id: int
    hotel_id: int
    role: UserRole

