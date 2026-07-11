import pytest
from unittest.mock import MagicMock

from src.domain.comercio.modelos.carrito import ArticuloCarrito, CalculoArticulo
from src.adapters.precios.servicios.cotizador import CotizadorServicio


def test_cotizador_servicio_exito_y_cache():
    # Simular cargador de tarifas
    tarifas_mock = {
        "tarifas": {
            "conceptos": {
                "base": 1.5,
                "manija": 0.5,
            }
        }
    }
    cargar_tarifas_fn = MagicMock(return_value=tarifas_mock)

    articulo_1 = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=100,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )
    articulo_2 = ArticuloCarrito(
        id=2,
        nombre="Bolsa B",
        descripcion="B",
        cantidad=200,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["manija"]),
    )

    servicio = CotizadorServicio(cargar_tarifas_yaml=cargar_tarifas_fn)

    # Cotizar primer artículo
    precio_1 = servicio.calcular_precio_estimado(articulo_1)
    assert precio_1 == 150.0  # 1.5 * 100
    assert cargar_tarifas_fn.call_count == 1

    # Cotizar segundo artículo (debe usar el caché y no volver a cargar las tarifas)
    precio_2 = servicio.calcular_precio_estimado(articulo_2)
    assert precio_2 == 100.0  # 0.5 * 200
    assert cargar_tarifas_fn.call_count == 1  # Sigue siendo 1!


def test_cotizador_servicio_error_cargador():
    cargar_tarifas_fn = MagicMock(side_effect=Exception("Falla de I/O"))
    registrar_error_fn = MagicMock()

    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=100,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )

    servicio = CotizadorServicio(
        cargar_tarifas_yaml=cargar_tarifas_fn,
        registrar_error=registrar_error_fn,
    )

    with pytest.raises(ValueError, match="No se pudieron obtener las tarifas de cotización"):
        servicio.calcular_precio_estimado(articulo)

    registrar_error_fn.assert_called_once()
