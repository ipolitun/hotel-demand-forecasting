from dataclasses import dataclass
from typing import Any


@dataclass
class FakeUser:
    id: int
    name: str
    surname: str
    email: str
    hashed_password: str
    is_active: bool = True
    # store enum value as string to avoid importing shared enums in tests
    system_role: str = "user"


@dataclass
class FakeUserHotel:
    user_id: int
    hotel_id: int
    role: Any  # enum or str


class FakeUserRepository:
    def __init__(self, users: dict[int, FakeUser] | None = None):
        self._users: dict[int, FakeUser] = users or {}
        self._by_email: dict[str, int] = {u.email: u.id for u in self._users.values()}

    async def create(
        self,
        name: str,
        surname: str,
        email: str,
        hashed_password: str,
        system_role: Any = "user",
        is_active: bool = True,
    ) -> FakeUser:
        new_id = max(self._users.keys(), default=0) + 1
        user = FakeUser(
            id=new_id,
            name=name,
            surname=surname,
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            system_role=getattr(system_role, "value", system_role),
        )
        self._users[new_id] = user
        self._by_email[email] = new_id
        return user

    async def get_by_id(self, user_id: int) -> FakeUser | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> FakeUser | None:
        uid = self._by_email.get(email)
        return self._users.get(uid) if uid is not None else None

    async def exists_by_id(self, user_id: int) -> bool:
        return user_id in self._users

    async def exists_by_email(self, email: str) -> bool:
        return email in self._by_email

    async def update_password(self, user_id: int, hashed_password: str) -> FakeUser | None:
        user = self._users.get(user_id)
        if not user:
            return None
        user.hashed_password = hashed_password
        return user

    async def deactivate(self, user_id: int) -> FakeUser | None:
        user = self._users.get(user_id)
        if not user:
            return None
        user.is_active = False
        return user


class FakeHotelRepository:
    def __init__(self):
        self._hotels: dict[int, Any] = {}

    async def create(self, **kwargs) -> Any:
        new_id = max(self._hotels.keys(), default=0) + 1
        hotel = type("Hotel", (), {"id": new_id, **kwargs})()
        self._hotels[new_id] = hotel
        return hotel

    async def get_by_id(self, hotel_id: int) -> Any | None:
        return self._hotels.get(hotel_id)

    async def exists_by_api_key(self, api_key: str) -> bool:
        return any(getattr(h, "api_key", None) == api_key for h in self._hotels.values())

    async def update_api_key(self, hotel_id: int, api_key: str) -> Any | None:
        hotel = self._hotels.get(hotel_id)
        if not hotel:
            return None
        setattr(hotel, "api_key", api_key)
        return hotel


class FakeUserHotelRepository:
    def __init__(self, links: list[FakeUserHotel] | None = None):
        self._links: list[FakeUserHotel] = links or []

    async def get_hotels_by_user(self, user_id: int) -> list[FakeUserHotel]:
        return [x for x in self._links if x.user_id == user_id]

    async def create(self, user_id: int, hotel_id: int, role: Any) -> FakeUserHotel:
        link = FakeUserHotel(user_id=user_id, hotel_id=hotel_id, role=role)
        self._links.append(link)
        return link

    async def update_role(self, user_id: int, hotel_id: int, role: Any) -> FakeUserHotel | None:
        for x in self._links:
            if x.user_id == user_id and x.hotel_id == hotel_id:
                x.role = role
                return x
        return None
