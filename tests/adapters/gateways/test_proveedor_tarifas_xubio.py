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
async def test_proveedor_tarifas_xubio_fallback_por_error():
    mock_gateway = AsyncMock()
    mock_gateway.proxy_request.side_effect = RuntimeError("Conexión rehusada")

    logger_mock = MagicMock()
    proveedor = ProveedorTarifasXubio(erp_gateway=mock_gateway, logger=logger_mock)
    tarifas = await proveedor.cargar_tarifas_async()

    # Debe devolver las tarifas por defecto de fallback
    assert "bobina_kg" in tarifas
    assert tarifas["bobina_kg"].monto == 1.0
    logger_mock.warning.assert_called_once()


def test_proveedor_tarifas_xubio_interfaz_sincronica():
    gateway = NullErpGateway()
    proveedor = ProveedorTarifasXubio(erp_gateway=gateway)
    tarifas = proveedor.obtener_tarifas()

    assert isinstance(tarifas, dict)
    assert "bobina_kg" in tarifas
