import pytest
from unittest.mock import MagicMock

from src.adapters.gateways.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from src.adapters.gateways.pricing_service import CotizadorServicio
from src.domain.commerce.cart import ArticuloCarrito, CalculoArticulo
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import (
    ComponenteBien,
    ProductoBien,
    ProductoServicio,
)
from src.domain.commerce.catalog import VariacionProducto


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


def test_cotizador_servicio_compuesto():
    catalogo = InMemoryCatalogRepository()
    servicio = CotizadorServicio(catalogo=catalogo)

    # Compuesto "Bolsa 12x8x19 cm Marrón con Manija Cordón Lisa 100g" (id 3001)
    articulo = ArticuloCarrito(
        id=3001,
        nombre="Bolsa 12x8x19 cm Marrón con Manija Cordón Lisa 100g",
        descripcion="Receta",
        cantidad=1000,
        imagen="bolsas-con-m.svg",
        calculo=None,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # Bolsa base (sin manija, lisa): base 0.15 * 1000 = 150
    # Manija cordón: 0.65 * 1000 = 650
    # Pegado: 0.10 * 1000 = 100
    assert precio == 900.0


def test_cotizador_servicio_compuesto_con_bobina_kg():
    catalogo = InMemoryCatalogRepository()
    servicio = CotizadorServicio(catalogo=catalogo)

    # Compuesto visible "Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g" (id 3004)
    articulo = ArticuloCarrito(
        id=3004,
        nombre="Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g",
        descripcion="Receta",
        cantidad=1000,
        imagen="bolsas-sin-m.svg",
        calculo=None,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # Bobina: kg_por_unidad(gramaje=100) ~= 0.02775 kg/u * 1000 u * $1.0/kg = 27.75
    # Confección: 0.08 * 1000 = 80
    assert round(precio, 2) == 107.75


def test_cotizador_servicio_bobina_simple_precio_por_kg():
    catalogo = InMemoryCatalogRepository()
    servicio = CotizadorServicio(catalogo=catalogo)

    # Variación de Bobina de Papel (id 76)
    articulo = ArticuloCarrito(
        id=76,
        nombre="Bobina de Papel",
        descripcion="Bobina",
        cantidad=500,
        imagen="bobina-de-papel.svg",
        calculo=catalogo.obtener_variacion_por_id(76)[1].calculo,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # 500 kg * $1.0/kg = 500
    assert precio == 500.0


def test_cotizador_servicio_cuerdas_de_papel_retorcidas():
    catalogo = InMemoryCatalogRepository()
    servicio = CotizadorServicio(catalogo=catalogo)

    # Producto compuesto "Cuerdas de Papel Retorcidas" (id 3005)
    articulo = ArticuloCarrito(
        id=3005,
        nombre="Cuerdas de Papel Retorcidas",
        descripcion="Receta",
        cantidad=1000,
        imagen="cuerdas-de-papel.svg",
        calculo=None,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # Bobina: 1 kg/unidad * 1000 unidades * $1.0/kg = 1000
    # Corte: 0.02 * 1000 = 20
    # Confección de cuerdas: 0.05 * 1000 = 50
    assert precio == 1070.0


def test_cotizador_servicio_con_catalogo_mock():
    variacion = VariacionProducto(
        id=1,
        sku="VAR",
        atributos={},
        imagen="img.png",
        cantidad_por_defecto=100,
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )
    simple = ProductoBien(
        tipo="bien",
        id=1001,
        nombre="Simple",
        descripcion="",
        imagen="img.png",
        atributos_posibles={},
        variaciones=[variacion],
        componentes=[],
    )
    servicio_model = ProductoServicio(
        tipo="servicio",
        id=2001,
        nombre="Servicio",
        descripcion="",
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["pegado"]),
    )
    compuesto = ProductoBien(
        tipo="bien",
        id=3001,
        nombre="Compuesto",
        descripcion="",
        imagen="img.png",
        cantidad_por_defecto=100,
        atributos_posibles={},
        variaciones=[],
        componentes=[
            ComponenteBien(tipo="variacion", referencia_id=1, cantidad=2, nombre="Simple"),
            ComponenteBien(tipo="servicio", referencia_id=2001, cantidad=1, nombre="Servicio"),
        ],
    )

    catalogo = MagicMock(spec=ICatalogRepository)
    catalogo.obtener_por_id.return_value = compuesto
    catalogo.resolver_componente.side_effect = lambda c: (
        variacion if c.tipo == "variacion" else servicio_model
    )

    servicio = CotizadorServicio(catalogo=catalogo)
    articulo = ArticuloCarrito(
        id=3001,
        nombre="Compuesto",
        descripcion="",
        cantidad=100,
        imagen="img.png",
        calculo=None,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # Variación factor 2: base 0.15 * 200 = 30
    # Servicio: pegado 0.10 * 100 = 10
    assert precio == 40.0
