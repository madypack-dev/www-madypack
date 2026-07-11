from typing import Any, Dict
import httpx
from src.domain.lead.http_client import IHttpClient, IHttpResponse


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

    async def post(
        self,
        url: str,
        headers: Dict[str, str] | None = None,
        json: Any = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout

        response = await self._client.post(
            url,
            headers=headers,
            json=json,
            **kwargs
        )
        return HttpxResponseAdapter(response)

    async def head(
        self,
        url: str,
        headers: Dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout

        response = await self._client.head(
            url,
            headers=headers,
            **kwargs
        )
        return HttpxResponseAdapter(response)
