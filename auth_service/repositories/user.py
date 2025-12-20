from abc import ABC, abstractmethod

from sqlalchemy import select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.schemas.roles import SystemRole

from shared.db_models import User


class IUserRepository(ABC):
    @abstractmethod
    async def create(
            self,
            name: str,
            surname: str,
            email: str,
            hashed_password: str,
            system_role: SystemRole = SystemRole.USER.value,
            is_active: bool = True,
    ) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def exists_by_id(self, user_id: int) -> bool:
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        pass

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> User | None:
        pass

    @abstractmethod
    async def deactivate(self, user_id: int) -> User | None:
        pass


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
            self,
            name: str,
            surname: str,
            email: str,
            hashed_password: str,
            system_role: SystemRole = SystemRole.USER.value,
            is_active: bool = True,
    ) -> User:
        new_user = User(
            name=name,
            surname=surname,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            system_role=system_role,
        )
        self._session.add(new_user)
        await self._session.flush()
        return new_user

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_id(self, user_id: int) -> bool:
        stmt = select(
            exists().where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(
            exists().where(User.email == email)
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def update_password(self, user_id: int, hashed_password: str) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed_password)
            .returning(User)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def deactivate(self, user_id: int) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
            .returning(User)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()
