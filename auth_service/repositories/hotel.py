from abc import ABC, abstractmethod

from sqlalchemy import select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import Hotel


class IHotelRepository(ABC):
    @abstractmethod
    async def create(self, name: str, is_city_hotel: bool, api_key: str, city_id: int = 1) -> Hotel | None:
        pass

    @abstractmethod
    async def get_by_id(self, hotel_id: int) -> Hotel | None:
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Hotel | None:
        pass

    @abstractmethod
    async def exists_by_id(self, hotel_id: int) -> bool:
        pass

    @abstractmethod
    async def exists_by_api_key(self, api_key: str) -> bool:
        pass

    @abstractmethod
    async def update_api_key(self, hotel_id: int, new_api_key: str) -> Hotel | None:
        pass


class HotelRepository(IHotelRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
            self,
            name: str,
            is_city_hotel: bool,
            api_key: str,
            city_id: int = 1,
    ) -> Hotel:
        new_hotel = Hotel(
            name=name,
            city_id=city_id,
            is_city_hotel=is_city_hotel,
            api_key=api_key,
        )
        self._session.add(new_hotel)
        await self._session.flush()
        return new_hotel

    async def get_by_id(self, hotel_id: int) -> Hotel | None:
        stmt = select(Hotel).where(Hotel.id == hotel_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> Hotel | None:
        stmt = select(Hotel).where(Hotel.api_key == api_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_id(self, hotel_id: int) -> bool:
        stmt = select(
            exists().where(Hotel.id == hotel_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def exists_by_api_key(self, api_key: str) -> bool:
        stmt = select(
            exists().where(Hotel.api_key == api_key)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def update_api_key(self, hotel_id: int, new_api_key: str) -> Hotel | None:
        stmt = (
            update(Hotel)
            .where(Hotel.id == hotel_id)
            .values(api_key=new_api_key)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
