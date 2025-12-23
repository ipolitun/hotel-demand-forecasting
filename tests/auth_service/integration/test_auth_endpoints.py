import pytest

pytestmark = [pytest.mark.auth, pytest.mark.integration]


async def test_login_sets_cookies(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "correct-password"},
    )
    assert resp.status_code == 200

    set_cookie = resp.headers.get_list("set-cookie")
    assert any(c.startswith("access_token=") for c in set_cookie)
    assert any(c.startswith("refresh_token=") for c in set_cookie)


async def test_login_invalid_password_returns_401(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    )
    assert resp.status_code in (401, 403)


async def test_refresh_rotates_tokens_and_sets_cookies(client):
    client.cookies.set("refresh_token", "refresh-token")
    resp = await client.post("/auth/refresh")

    assert resp.status_code == 200
    set_cookie = resp.headers.get_list("set-cookie")
    assert any(c.startswith("access_token=") for c in set_cookie)
    assert any(c.startswith("refresh_token=") for c in set_cookie)


async def test_refresh_missing_cookie_returns_401(client):
    resp = await client.post("/auth/refresh")
    assert resp.status_code in (401, 403)


async def test_change_password_clears_cookies_and_revokes_tokens(client, principal_headers, fake_auth_service):
    client.cookies.set("access_token", "a")
    client.cookies.set("refresh_token", "refresh-token")

    resp = await client.post(
        "/auth/change-password",
        headers=principal_headers,
        json={
            "current_password": "correct-password",
            "new_password": "new-strong-password"
        },
    )
    assert resp.status_code == 200
    assert "1" in fake_auth_service.revoked_all

    set_cookie = resp.headers.get_list("set-cookie")
    assert any(c.startswith("access_token=") for c in set_cookie)
    assert any(c.startswith("refresh_token=") for c in set_cookie)


async def test_logout_clears_cookies_and_revokes_one_token(client, fake_auth_service):
    client.cookies.set("refresh_token", "refresh-token")
    resp = await client.post("/auth/logout")

    assert resp.status_code == 204
    assert ("jti-1", "1") in fake_auth_service.revoked

    set_cookie = resp.headers.get_list("set-cookie")
    assert any(c.startswith("access_token=") for c in set_cookie)
    assert any(c.startswith("refresh_token=") for c in set_cookie)


async def test_logout_all_revokes_all_tokens(client, principal_headers, fake_auth_service):
    client.cookies.set("refresh_token", "refresh-token")
    resp = await client.post(
        "/auth/logout/all",
        headers=principal_headers,
    )
    assert resp.status_code == 204
    assert "1" in fake_auth_service.revoked_all
