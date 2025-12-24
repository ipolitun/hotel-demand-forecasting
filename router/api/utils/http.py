from fastapi import Response
import httpx

from shared.errors import ExternalServiceError


def forward_response(
    *,
    source: httpx.Response,
    target: Response,
) -> None:
    """
    Проксирует HTTP-ответ downstream-сервиса
    в ответ API Gateway.

    Копирует:
    - HTTP status code
    - тело ответа (body)
    - заголовок Content-Type
    - все заголовки Set-Cookie

    Не выполняет интерпретацию или модификацию ответа.
    """
    target.status_code = source.status_code
    target.body = source.content

    content_type = source.headers.get("content-type")
    if content_type:
        target.headers["content-type"] = content_type

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