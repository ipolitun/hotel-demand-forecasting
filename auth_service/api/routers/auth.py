from fastapi import Depends, APIRouter, Response
from starlette import status

from auth_service.api.cookies import set_auth_cookies, clear_auth_cookies
from auth_service.api.dependencies import (
    get_uow,
    get_token_auth_service,
    get_principal,
    get_refresh_cookie,
)
from auth_service.repositories.unit_of_work import IUnitOfWork
from auth_service.schemas.auth import AuthPrincipal
from auth_service.schemas.user import UserCredentials, PasswordUpdate
from auth_service.services.token.jwt_auth import JWTAuthService
from auth_service.use_cases.authenticate import authenticate
from auth_service.use_cases.change_password import change_password
from auth_service.use_cases.logout import logout, logout_all
from auth_service.use_cases.rotate_tokens import rotate_tokens

from shared.errors import register_errors, AuthorizationError, ConflictError

router = APIRouter()


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя в систему",
)
@register_errors(AuthorizationError)
async def login_endpoint(
        credentials: UserCredentials,
        response: Response,
        uow: IUnitOfWork = Depends(get_uow),
        auth_service: JWTAuthService = Depends(get_token_auth_service)
):
    principal = await authenticate(
        credentials=credentials,
        uow=uow,
    )
    access, refresh = await auth_service.generate_tokens(principal=principal)

    set_auth_cookies(
        response,
        access_token=access,
        refresh_token=refresh,
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление пары access/refresh токенов",
)
@register_errors(AuthorizationError)
async def refresh_endpoint(
        response: Response,
        refresh_token: str = Depends(get_refresh_cookie),
        uow: IUnitOfWork = Depends(get_uow),
        auth_service: JWTAuthService = Depends(get_token_auth_service)
):
    access, refresh = await rotate_tokens(
        refresh_token=refresh_token,
        uow=uow,
        auth=auth_service,
    )

    set_auth_cookies(
        response,
        access_token=access,
        refresh_token=refresh,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Смена пароля пользователя",
)
@register_errors(AuthorizationError, ConflictError)
async def change_password_endpoint(
        response: Response,
        data: PasswordUpdate,
        principal: AuthPrincipal = Depends(get_principal),
        uow: IUnitOfWork = Depends(get_uow),
        auth_service: JWTAuthService = Depends(get_token_auth_service),
):
    await change_password(
        user_id=principal.user_id,
        passwords_data=data,
        uow=uow,
    )
    await auth_service.revoke_all_tokens(user_id=str(principal.user_id))
    clear_auth_cookies(response)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
@register_errors(AuthorizationError)
async def logout_endpoint(
        response: Response,
        refresh_token: str = Depends(get_refresh_cookie),
        auth_service: JWTAuthService = Depends(get_token_auth_service),
):
    await logout(
        refresh_token=refresh_token,
        auth=auth_service,
    )
    clear_auth_cookies(response)


@router.post(
    "/logout/all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход со всех устройств",
)
async def logout_all_endpoint(
        response: Response,
        refresh_token: str = Depends(get_refresh_cookie),
        principal: AuthPrincipal = Depends(get_principal),
        auth_service: JWTAuthService = Depends(get_token_auth_service),
):
    await logout_all(
        refresh_token=refresh_token,
        user_id=principal.user_id,
        auth=auth_service,
    )
    clear_auth_cookies(response)
