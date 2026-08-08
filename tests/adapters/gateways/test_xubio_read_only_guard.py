"""Tests unitarios para verificar la guardia de solo lectura (GET únicamente) en Xubio ERP."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.check_xubio_read_only import verificar_solo_lectura_xubio
from src.adapters.gateways.xubio_client import XubioErpGateway


def test_guardia_ast_verificar_solo_lectura():
    archivos = [
        Path("src/adapters/gateways/xubio_client.py"),
        Path("src/infrastructure/fastapi/routes/xubio_replica.py"),
    ]
    assert verificar_solo_lectura_xubio(archivos) is True


@pytest.mark.asyncio
async def test_xubio_gateway_proxy_request_permite_get():
    mock_client = AsyncMock()

    res_get = MagicMock()
    res_get.status_code = 200
    res_get.json.return_value = {"status": "ok"}

    res_post = MagicMock()
    res_post.status_code = 200
    res_post.json.return_value = {"access_token": "dummy_token"}

    mock_client.request.return_value = res_get
    mock_client.post.return_value = res_post

    gateway = XubioErpGateway(client=mock_client)
    res = await gateway.proxy_request("GET", "/miempresa")
    assert res == {"status": "ok"}
