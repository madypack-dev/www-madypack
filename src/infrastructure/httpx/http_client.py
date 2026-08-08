from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from src.domain.lead.http_client import IHttpClient, IHttpResponse


@asynccontextmanager
async def crear_cliente_http_async(timeout: float = 10.0) -> AsyncGenerator[IHttpClient, None]:
    """Context manager asíncrono que administra la sesión del cliente HTTP sin exponer httpx."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield HttpxClientAdapter(client)


class HttpxResponseAdapter(IHttpResponse):
    """Adaptador para la respuesta de httpx."""

    def __init__(self, response: httpx.Response):
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    def json(self) -> Any:
        return self._response.json()

    def raise_for_status(self) -> None:
        self._response.raise_for_status()


class HttpxClientAdapter(IHttpClient):
    """Adaptador de cliente HTTP que utiliza httpx.AsyncClient bajo el capó."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if params is not None:
            kwargs["params"] = params

        response = await self._client.get(url, headers=headers, **kwargs)
        return HttpxResponseAdapter(response)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any = None,
        content: str | bytes | None = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if content is not None:
            kwargs["content"] = content
        if json is not None:
            kwargs["json"] = json

        response = await self._client.post(url, headers=headers, **kwargs)
        return HttpxResponseAdapter(response)

    async def head(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout

        response = await self._client.head(url, headers=headers, **kwargs)
        return HttpxResponseAdapter(response)

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any = None,
        content: str | bytes | None = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if params is not None:
            kwargs["params"] = params
        if json is not None:
            kwargs["json"] = json
        if content is not None:
            kwargs["content"] = content

        response = await self._client.request(method=method, url=url, headers=headers, **kwargs)
        return HttpxResponseAdapter(response)
