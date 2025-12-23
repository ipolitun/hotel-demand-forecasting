import pytest

pytestmark = [pytest.mark.auth, pytest.mark.integration]


async def test_register_user_success(client):
    resp = await client.post(
        "/users/users/register",
        json={
            "name": "Alice",
            "surname": "Smith",
            "email": "alice@example.com",
            "password": "very-strong-password",
        },
    )
    # should return 201 with user payload
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert data["is_active"] is True


async def test_register_user_conflict_returns_409(client):
    # register same email twice
    await client.post(
        "/users/users/register",
        json={
            "name": "Bob",
            "surname": "Smith",
            "email": "bob@example.com",
            "password": "very-strong-password",
        },
    )
    resp2 = await client.post(
        "/users/users/register",
        json={
            "name": "Bob",
            "surname": "Smith",
            "email": "bob@example.com",
            "password": "very-strong-password",
        },
    )
    assert resp2.status_code == 409
