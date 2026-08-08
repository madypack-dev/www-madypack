"""Tests unitarios para la capa de infraestructura HTTP (src/infrastructure/httpx/http_client.py)."""

import pytest

from src.infrastructure.httpx.http_client import HttpxClientAdapter, crear_cliente_http_async


@pytest.mark.asyncio
async def test_crear_cliente_http_async_context_manager():
    async with crear_cliente_http_async(timeout=5.0) as adapter:
        assert isinstance(adapter, HttpxClientAdapter)
