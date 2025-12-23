from .repositories import (
    FakeUserRepository,
    FakeHotelRepository,
    FakeUserHotelRepository
)


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        users: FakeUserRepository | None = None,
        hotels: FakeHotelRepository | None = None,
        users_hotels: FakeUserHotelRepository | None = None,
    ):
        self._users = users or FakeUserRepository()
        self._hotels = hotels or FakeHotelRepository()
        self._users_hotels = users_hotels or FakeUserHotelRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()

    @property
    def users(self) -> FakeUserRepository:
        return self._users

    @property
    def hotels(self) -> FakeHotelRepository:
        return self._hotels

    @property
    def users_hotels(self) -> FakeUserHotelRepository:
        return self._users_hotels

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
