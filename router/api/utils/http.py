from fastapi import Response
import httpx

from shared.errors import ExternalServiceError


def forward_response(
    *,
    source: httpx.Response,
    target: Response,
) -> None:
    """
    Проксирует HTTP-атрибуты ответа downstream-сервиса
    в HTTP-ответ API Gateway.

    Forward:
    - status_code
    - Set-Cookie headers

    Не изменяет body.
    """
    target.status_code = source.status_code

    for cookie in source.headers.get_list("set-cookie"):
        target.headers.append("set-cookie", cookie)


async def proxy_post(
    *,
    client: httpx.AsyncClient,
    url: str,
    **kwargs,
) -> httpx.Response:
    try:
        return await client.post(url, **kwargs)
    except httpx.RequestError as exc:
        raise ExternalServiceError("Downstream service unavailable") from exc