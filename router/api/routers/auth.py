import logging

import httpx
from fastapi import APIRouter, Response, Depends, status

from router.api.dependencies import (
    get_http_client,
    get_jwt_principal,
)
from router.api.schemas import (
    PasswordUpdateRequest,
    UserLoginRequest,
    UserRegisterResponse,
    UserRegisterRequest,
)
from router.api.utils.http import forward_response, proxy_post
from router.config import router_config
from shared.errors import (
    register_errors,
    AuthorizationError,
    ExternalServiceError,
    ConflictError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def login(
        data: UserLoginRequest,
        response: Response,
        client: httpx.AsyncClient = Depends(get_http_client),
):
    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/auth/login",
        json=data.model_dump(),
    )

    forward_response(source=auth_response, target=response)
    return response


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление access/refresh токенов",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def refresh(
        response: Response,
        client: httpx.AsyncClient = Depends(get_http_client),
):
    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/auth/refresh",
    )

    forward_response(source=auth_response, target=response)
    return response


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Смена пароля пользователя",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def change_password(
        data: PasswordUpdateRequest,
        response: Response,
        principal: dict = Depends(get_jwt_principal),
        client: httpx.AsyncClient = Depends(get_http_client),
):
    headers = {"X-User-Id": principal["sub"]}

    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/auth/change-password",
        headers=headers,
        json=data.model_dump(),
    )

    forward_response(source=auth_response, target=response)
    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def logout(
        response: Response,
        client: httpx.AsyncClient = Depends(get_http_client),
):
    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/auth/logout",
    )

    forward_response(source=auth_response, target=response)
    return response


@router.post(
    "/logout/all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход со всех устройств",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def logout_all(
        response: Response,
        principal: dict = Depends(get_jwt_principal),
        client: httpx.AsyncClient = Depends(get_http_client),
):
    headers = {
        "X-User-Id": principal["sub"],
    }

    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/auth/logout/all",
        headers=headers,
    )

    forward_response(source=auth_response, target=response)
    return response


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя в системе",
)
@register_errors(ConflictError, ExternalServiceError)
async def register_user(
        response: Response,
        data: UserRegisterRequest,
        client: httpx.AsyncClient = Depends(get_http_client),
):
    auth_response = await proxy_post(
        client=client,
        url=f"{router_config.auth_service_url}/users/register",
        json=data.model_dump(),
    )

    forward_response(source=auth_response, target=response)
    return response


@router.get(
    "/me",
    summary="Текущий пользователь",
)
@register_errors(AuthorizationError, ExternalServiceError)
async def get_me(
        payload: dict = Depends(get_jwt_principal),
):
    # TODO: в будущем редиректить в 'auth_service/auth/me'
    return payload
