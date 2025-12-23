import pytest

from auth_service.schemas.user import UserCredentials, PasswordUpdate
from auth_service.use_cases.authenticate import authenticate
from auth_service.use_cases.rotate_tokens import rotate_tokens
from auth_service.use_cases.change_password import change_password
from auth_service.use_cases.logout import logout, logout_all

from shared.errors import AuthorizationError, ConflictError


pytestmark = [pytest.mark.auth, pytest.mark.unit]


async def test_authenticate_success(fake_uow):
    principal = await authenticate(
        credentials=UserCredentials(email="test@example.com", password="correct-password"),
        uow=fake_uow,
    )
    assert principal.user_id == 1
    assert len(principal.hotels) == 1


async def test_authenticate_invalid_password_raises(fake_uow):
    with pytest.raises(AuthorizationError):
        await authenticate(
            credentials=UserCredentials(email="test@example.com", password="wrong-password"),
            uow=fake_uow,
        )


async def test_rotate_tokens_invalid_payload_raises(fake_uow, fake_auth_service):
    # token not seeded -> read_token returns None -> invalid payload
    with pytest.raises(AuthorizationError):
        await rotate_tokens(
            refresh_token="unknown-token",
            uow=fake_uow,
            auth=fake_auth_service,
        )


async def test_change_password_conflict_same_password(fake_uow):
    # new password equals current should raise ConflictError
    with pytest.raises(ConflictError):
        await change_password(
            user_id=1,
            passwords_data=PasswordUpdate(
                current_password="correct-password",
                new_password="correct-password",
            ),
            uow=fake_uow,
        )


async def test_logout_all_sub_mismatch_raises(fake_auth_service):
    # seed token for another user
    from auth_service.schemas.token import TokenRefreshPayload, TokenType
    fake_auth_service.seed_refresh_payload(
        "rt2",
        TokenRefreshPayload(sub="2", token_type=TokenType.REFRESH, jti="jti-2", exp=9999999999),
    )
    with pytest.raises(AuthorizationError):
        await logout_all(user_id=1, refresh_token="rt2", auth=fake_auth_service)
