from datetime import date
from decimal import Decimal

import pytest
from unittest.mock import MagicMock

from src.adapters.gateways.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from src.adapters.gateways.proveedor_ipc_default import ProveedorIPCDefault
from src.adapters.gateways.proveedor_tasa_cambio_default import ProveedorTasaCambioDefault
from src.adapters.gateways.proveedor_tarifas_default import ProveedorTarifasDefault
from src.application.quote.pricing_service import CotizadorServicio
from src.domain.commerce.cart import ArticuloCarrito, CalculoArticulo
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import (
    ComponenteBien,
    ProductoBien,
    ProductoServicio,
)
from src.domain.commerce.catalog import VariacionProducto
from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.proveedor_ipc import IProveedorIPC
from src.domain.pricing.proveedor_tarifas import IProveedorTarifas
from src.domain.pricing.proveedor_tasa_cambio import IProveedorTasaCambio
from src.domain.pricing.tasa_cambio import TasaCambio


class _ProveedorTasaFija:
    def __init__(self, tasa: TasaCambio):
        self._tasa = tasa

    def obtener_tasa(self) -> TasaCambio:
        return self._tasa


class _ProveedorTarifasFijo:
    def __init__(self, tarifas: dict[str, ConceptoTarifa]):
        self._tarifas = tarifas

    def obtener_tarifas(self) -> dict[str, ConceptoTarifa]:
        return self._tarifas


class _ProveedorIPCFijo:
    def __init__(self, factor: Decimal):
        self._factor = factor

    def obtener_factor(self, desde: date, hasta: date) -> Decimal:
        return self._factor


def _cotizador_default(
    catalogo=None,
    registrar_error=None,
    proveedor_tarifas: IProveedorTarifas | None = None,
    proveedor_tasa: IProveedorTasaCambio | None = None,
    proveedor_ipc: IProveedorIPC | None = None,
    fecha_presente: date = date(2024, 1, 1),
    bolsa_solap_cm: float = 3.5,
):
    return CotizadorServicio(
        catalogo=catalogo,
        registrar_error=registrar_error or (lambda _: None),
        proveedor_tarifas=proveedor_tarifas or ProveedorTarifasDefault(),
        proveedor_tasa=proveedor_tasa or ProveedorTasaCambioDefault(),
        proveedor_ipc=proveedor_ipc or ProveedorIPCDefault(),
        fecha_presente=fecha_presente,
        bolsa_solap_cm=bolsa_solap_cm,
    )


def test_cotizador_servicio_exito():
    articulo_1 = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )
    servicio = _cotizador_default()
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
    servicio = _cotizador_default(registrar_error=registrar_error_fn)

    with pytest.raises(ValueError):
        servicio.calcular_precio_estimado(articulo)

    registrar_error_fn.assert_called_once()


def test_cotizador_servicio_compuesto():
    catalogo = InMemoryCatalogRepository()
    servicio = _cotizador_default(catalogo=catalogo)

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
    # Manija cordón 114mm (formato para ancho 12cm): 0.000912 * 1000 = 0.912
    # Pegado: 0.10 * 1000 = 100
    assert round(precio, 3) == 250.912


def test_cotizador_servicio_compuesto_con_bobina_kg():
    catalogo = InMemoryCatalogRepository()
    servicio = _cotizador_default(catalogo=catalogo)

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
    servicio = _cotizador_default(catalogo=catalogo)

    # Variación de Bobina de Papel
    bobina = catalogo.obtener_por_id(1104)
    assert isinstance(bobina, ProductoBien)
    variacion_bobina = bobina.variaciones[0]
    articulo = ArticuloCarrito(
        id=variacion_bobina.id,
        nombre="Bobina de Papel",
        descripcion="Bobina",
        cantidad=500,
        imagen="bobina-de-papel.svg",
        calculo=variacion_bobina.calculo,
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # 500 kg * $1.0/kg = 500
    assert precio == 500.0


def test_cotizador_servicio_cuerdas_de_papel_retorcidas():
    catalogo = InMemoryCatalogRepository()
    servicio = _cotizador_default(catalogo=catalogo)

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

    servicio = _cotizador_default(catalogo=catalogo)
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


def test_cotizador_servicio_usa_solapa_configurable():
    catalogo = InMemoryCatalogRepository()
    servicio_default = _cotizador_default(catalogo=catalogo, bolsa_solap_cm=3.5)
    servicio_mayor_solapa = _cotizador_default(catalogo=catalogo, bolsa_solap_cm=4.5)

    # Compuesto visible "Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g" (id 3004)
    articulo = ArticuloCarrito(
        id=3004,
        nombre="Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g",
        descripcion="Receta",
        cantidad=1000,
        imagen="bolsas-sin-m.svg",
        calculo=None,
    )

    precio_default = servicio_default.calcular_precio_estimado(articulo)
    precio_mayor_solapa = servicio_mayor_solapa.calcular_precio_estimado(articulo)

    # Al aumentar la solapa, el consumo de bobina (y el precio) debe subir
    assert precio_mayor_solapa > precio_default


def test_cotizador_servicio_concepto_usd_se_convierte_a_ars():
    tasa = TasaCambio(fecha=date(2024, 6, 1), ars_por_usd=1000.0, fuente="BNA")
    tarifas = {
        "base": ConceptoTarifa(nombre="base", monto=0.10, moneda=Moneda.USD, fecha=date(2024, 1, 1)),
    }
    servicio = _cotizador_default(
        proveedor_tarifas=_ProveedorTarifasFijo(tarifas),
        proveedor_tasa=_ProveedorTasaFija(tasa),
    )
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # 0.10 USD/u * 1000 ARS/USD * 1000 unidades = 100000 ARS
    assert precio == 100000.0


def test_cotizador_servicio_sin_proveedor_tasa_asume_paridad_para_usd():
    """Sin proveedor de tasa explícito, se usa la tasa default (paridad 1:1)."""
    tarifas = {
        "base": ConceptoTarifa(nombre="base", monto=0.10, moneda=Moneda.USD, fecha=date(2024, 1, 1)),
    }
    servicio = _cotizador_default(
        proveedor_tarifas=_ProveedorTarifasFijo(tarifas),
    )
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )

    precio = servicio.calcular_precio_estimado(articulo)

    assert precio == 100.0


def test_cotizador_servicio_actualiza_concepto_ars_por_ipc():
    """Una tarifa ARS de fecha anterior con IPC acumulado se actualiza a valor presente."""
    tarifas = {
        "base": ConceptoTarifa(nombre="base", monto=0.10, moneda=Moneda.ARS, fecha=date(2024, 1, 1)),
    }
    servicio = _cotizador_default(
        proveedor_tarifas=_ProveedorTarifasFijo(tarifas),
        proveedor_ipc=_ProveedorIPCFijo(Decimal("1.21")),
        fecha_presente=date(2024, 6, 1),
    )
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # 0.10 ARS/u * 1.21 (IPC) * 1000 unidades = 121.0 ARS
    assert precio == 121.0


def test_cotizador_servicio_no_actualiza_usd_por_ipc():
    """Los conceptos en USD se convierten al tipo de cambio y no se reescalan por IPC."""
    tarifas = {
        "base": ConceptoTarifa(nombre="base", monto=0.10, moneda=Moneda.USD, fecha=date(2024, 1, 1)),
    }
    tasa = TasaCambio(fecha=date(2024, 6, 1), ars_por_usd=1000.0, fuente="BNA")
    servicio = _cotizador_default(
        proveedor_tarifas=_ProveedorTarifasFijo(tarifas),
        proveedor_tasa=_ProveedorTasaFija(tasa),
        proveedor_ipc=_ProveedorIPCFijo(Decimal("1.21")),
        fecha_presente=date(2024, 6, 1),
    )
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa A",
        descripcion="A",
        cantidad=1000,
        imagen="img.png",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
    )

    precio = servicio.calcular_precio_estimado(articulo)

    # 0.10 USD/u * 1000 ARS/USD * 1000 unidades = 100000 ARS (sin IPC)
    assert precio == 100000.0
