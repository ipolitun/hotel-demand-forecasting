from abc import ABC, abstractmethod
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.schemas.roles import UserRole

from shared.db_models import UserHotel


class IUserHotelRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int, hotel_id: int, role: UserRole) -> UserHotel:
        pass

    @abstractmethod
    async def get(self, user_id: int, hotel_id: int) -> UserHotel | None:
        pass

    @abstractmethod
    async def get_hotels_by_user(self, user_id: int) -> Sequence[UserHotel]:
        pass

    @abstractmethod
    async def get_users_by_hotel(self, hotel_id: int) -> Sequence[UserHotel]:
        pass

    @abstractmethod
    async def update_role(self, user_id: int, hotel_id: int, role: UserRole) -> UserHotel | None:
        pass


class UserHotelRepository(IUserHotelRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_id: int, hotel_id: int, role: UserRole) -> UserHotel:
        user_hotel = UserHotel(user_id=user_id, hotel_id=hotel_id, role=role)
        self._session.add(user_hotel)
        await self._session.flush()
        return user_hotel

    async def get(self, user_id: int, hotel_id: int) -> UserHotel | None:
        stmt = select(UserHotel).where(
            UserHotel.user_id == user_id,
            UserHotel.hotel_id == hotel_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_hotels_by_user(self, user_id: int) -> Sequence[UserHotel]:
        stmt = select(UserHotel).where(UserHotel.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_users_by_hotel(self, hotel_id: int) -> Sequence[UserHotel]:
        stmt = select(UserHotel).where(UserHotel.hotel_id == hotel_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_role(self, user_id: int, hotel_id: int, role: UserRole) -> UserHotel | None:
        stmt = (
            update(UserHotel)
            .where(UserHotel.user_id == user_id, UserHotel.hotel_id == hotel_id)
            .values(role=role)
            .returning(UserHotel)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()
