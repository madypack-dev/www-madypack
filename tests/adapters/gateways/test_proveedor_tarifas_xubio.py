"""Tests unitarios para ProveedorTarifasXubio."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.adapters.gateways.proveedor_tarifas_xubio import ProveedorTarifasXubio


@pytest.mark.asyncio
async def test_proveedor_tarifas_xubio_exito():
    mock_gateway = AsyncMock()
    mock_gateway.proxy_request.return_value = {
        "listaPrecioItem": [
            {"codigo": "bobina_kg", "precio": 1500.0},
            {"codigo": "confeccion", "precio": 120.0},
        ]
    }

    proveedor = ProveedorTarifasXubio(erp_gateway=mock_gateway)
    tarifas = await proveedor.cargar_tarifas_async()

    assert "bobina_kg" in tarifas
    assert tarifas["bobina_kg"].monto == 1500.0
    assert "confeccion" in tarifas
    assert tarifas["confeccion"].monto == 120.0


@pytest.mark.asyncio
async def test_proveedor_tarifas_xubio_error_devuelve_vacio_sin_fallback():
    mock_gateway = AsyncMock()
    mock_gateway.proxy_request.side_effect = RuntimeError("Conexión rehusada")

    logger_mock = MagicMock()
    proveedor = ProveedorTarifasXubio(erp_gateway=mock_gateway, logger=logger_mock)
    tarifas = await proveedor.cargar_tarifas_async()

    # Al eliminar el fallback de $1.00, debe devolver un diccionario vacío si falla Xubio
    assert tarifas == {}
    logger_mock.warning.assert_called_once()


def test_proveedor_tarifas_xubio_interfaz_sincronica():
    gateway = NullErpGateway()
    proveedor = ProveedorTarifasXubio(erp_gateway=gateway)
    tarifas = proveedor.obtener_tarifas()

    assert isinstance(tarifas, dict)
