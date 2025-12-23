import json

import pytest
from httpx import AsyncClient, ASGITransport

from auth_service.api.dependencies import get_uow, get_token_auth_service
from auth_service.main import create_app

from faces.jwt_auth_service import FakeJWTAuthService
from faces.repositories import FakeUserRepository, FakeUser, FakeUserHotelRepository, FakeUserHotel
from faces.unit_of_work import FakeUnitOfWork


@pytest.fixture
def fake_uow():
    from auth_service.utils.password import hash_password

    pwd = hash_password("correct-password")
    user_repo = FakeUserRepository(
        users={
            1: FakeUser(
                id=1,
                name="Test",
                surname="User",
                email="test@example.com",
                hashed_password=pwd,
                is_active=True,
                system_role="user",
            )
        }
    )
    users_hotels_repo = FakeUserHotelRepository(
        links=[FakeUserHotel(user_id=1, hotel_id=101, role="owner")]
    )
    return FakeUnitOfWork(users=user_repo, users_hotels=users_hotels_repo)


@pytest.fixture
def fake_auth_service():
    from auth_service.schemas.token import TokenRefreshPayload, TokenType

    svc = FakeJWTAuthService()
    svc.seed_refresh_payload(
        "refresh-token",
        TokenRefreshPayload(sub="1", token_type=TokenType.REFRESH, jti="jti-1", exp=9999999999),
    )
    return svc


@pytest.fixture
def app(fake_uow, fake_auth_service):
    app = create_app()

    app.dependency_overrides[get_uow] = lambda: fake_uow
    app.dependency_overrides[get_token_auth_service] = lambda: fake_auth_service

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def principal_headers():
    return {"X-User-Id": "1"}


@pytest.fixture
def hotel_principal_headers():
    hotels = [{"id": 101, "user_role": "owner"}]
    return {
        "X-User-Id": "1",
        "X-System-Role": "user",
        "X-Hotels": json.dumps(hotels),
    }
