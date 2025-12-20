from fastapi import Response

from auth_service.config import auth_config


def set_auth_cookies(
        response: Response,
        *,
        access_token: str,
        refresh_token: str,
) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        max_age=auth_config.access_token_expire_minutes * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        max_age=auth_config.refresh_token_expire_minutes * 60,
        path="/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth")
