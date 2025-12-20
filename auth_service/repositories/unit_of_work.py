from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.repositories import (
    UserRepository,
    HotelRepository,
    UserHotelRepository,
)
from auth_service.repositories import (
    IUserRepository,
    IHotelRepository,
    IUserHotelRepository,
)
from shared.db import AsyncSessionLocal


class IUnitOfWork(ABC):
    @property
    @abstractmethod
    def users(self) -> IUserRepository:
        pass

    @property
    @abstractmethod
    def hotels(self) -> IHotelRepository:
        pass

    @property
    @abstractmethod
    def users_hotels(self) -> IUserHotelRepository:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def commit(self):
        await self._commit()

    @abstractmethod
    async def rollback(self):
        pass

    @abstractmethod
    async def _commit(self):
        pass


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal):
        self._session_factory = session_factory

    async def __aenter__(self):
        self.session: AsyncSession = self._session_factory()
        self._users = UserRepository(self.session)
        self._hotels = HotelRepository(self.session)
        self._users_hotels = UserHotelRepository(self.session)
        return self

    @property
    def users(self) -> UserRepository:
        return self._users

    @property
    def hotels(self) -> HotelRepository:
        return self._hotels

    @property
    def users_hotels(self) -> UserHotelRepository:
        return self._users_hotels

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def rollback(self):
        await self.session.rollback()

    async def _commit(self):
        await self.session.commit()
