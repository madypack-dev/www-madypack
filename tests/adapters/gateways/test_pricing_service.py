import pytest
from unittest.mock import MagicMock

from src.domain.commerce.cart import ArticuloCarrito, CalculoArticulo
from src.adapters.gateways.pricing_service import CotizadorServicio


def test_cotizador_servicio_exito():
    articulo_1 = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )
    servicio = CotizadorServicio()
    precio = servicio.calcular_precio_estimado(articulo_1)
    # base es 0.15 en tarifas fijas -> 0.15 * 1000 = 150.0
    assert precio == 150.0


def test_cotizador_servicio_error_calculo_nulo():
    registrar_error_fn = MagicMock()
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=100,
        imagen="img.png",
        calculo=None,
    )
    servicio = CotizadorServicio(registrar_error=registrar_error_fn)

    with pytest.raises(ValueError):
        servicio.calcular_precio_estimado(articulo)

    registrar_error_fn.assert_called_once()
