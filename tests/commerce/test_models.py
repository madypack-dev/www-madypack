import pytest
from pydantic import ValidationError

from src.domain.commerce.cart import Carrito, ArticuloCarrito, CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import (
    ComponenteBien,
    MedidasBolsa,
    ProductoBien,
    ProductoServicio,
)


def test_calculo_articulo():
    calculo = CalculoArticulo(tipo="unidad", conceptos=["base"], concepto_fijo="fijo")
    assert calculo.tipo == "unidad"
    assert "base" in calculo.conceptos
    assert calculo.concepto_fijo == "fijo"


def test_articulo_carrito_valido():
    articulo = ArticuloCarrito(
        id=1,
        nombre="Bolsa",
        descripcion="Bolsa de papel",
        cantidad=100,
        imagen="imagen.png"
    )
    assert articulo.id == 1
    assert articulo.cantidad == 100


def test_articulo_carrito_cantidad_invalida_no_multiplo():
    with pytest.raises(ValidationError) as exc_info:
        ArticuloCarrito(
            id=1,
            nombre="Bolsa",
            descripcion="Bolsa de papel",
            cantidad=150,
            imagen="imagen.png"
        )
    assert "La cantidad debe ser múltiplo de 100." in str(exc_info.value)


def test_articulo_carrito_cantidad_invalida_menor_que_100():
    with pytest.raises(ValidationError):
        ArticuloCarrito(
            id=1,
            nombre="Bolsa",
            descripcion="Bolsa de papel",
            cantidad=50,
            imagen="imagen.png"
        )


def test_carrito_operaciones():
    carrito = Carrito()
    assert carrito.total_bolsas == 0
    assert carrito.total_lineas == 0

    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    art2 = ArticuloCarrito(id=2, nombre="Bolsa B", descripcion="B", cantidad=200, imagen="img.png")

    carrito.agregar_articulo(art1)
    assert carrito.total_bolsas == 100
    assert carrito.total_lineas == 1

    # Agregar el mismo artículo incrementa cantidad
    carrito.agregar_articulo(art1)
    assert carrito.total_bolsas == 200

    carrito.agregar_articulo(art2)
    assert carrito.total_bolsas == 400

    # Actualizar cantidad
    assert carrito.actualizar_cantidad(1, 300) is True
    assert carrito.total_bolsas == 500

    # Actualizar artículo inexistente
    assert carrito.actualizar_cantidad(99, 100) is False

    # Eliminar artículo
    assert carrito.eliminar_articulo(1) is True
    assert carrito.total_bolsas == 200
    assert carrito.eliminar_articulo(99) is False


def test_medidas_bolsa_kg_por_unidad():
    medidas = MedidasBolsa(ancho=22, fuelle=10, alto=30)
    kg = medidas.kg_por_unidad(gramaje=100, solap_cm=3.5, rendimiento=0.9)

    # ancho_bobina = 22*2 + 10*2 + 3.5 = 67.5 cm
    # largo_cutoff = 30 + 10/2 + 2 = 37 cm
    # superficie = 0.675 * 0.37 = 0.24975 m²
    # peso_g = 0.24975 * 100 = 24.975 g
    # peso_kg = 0.024975
    # kg / rendimiento = 0.02775...
    assert kg > 0
    assert round(kg, 5) == 0.02775


def test_producto_bien_simple():
    variacion = VariacionProducto(
        id=1,
        sku="B-001",
        atributos={"color": "Marrón"},
        imagen="bolsa.svg",
        cantidad_por_defecto=1000,
        visible=True,
    )
    producto = ProductoBien(
        tipo="bien",
        id=1001,
        nombre="Bolsa de Papel",
        descripcion="Bolsa kraft",
        slug="bolsa-de-papel",
        imagen="bolsa.svg",
        atributos_posibles={"color": ["Marrón"]},
        variaciones=[variacion],
        componentes=[],
        visible=True,
    )
    assert producto.tipo == "bien"
    assert not producto.es_compuesto
    assert producto.url_slug == "bolsa-de-papel"
    assert producto.imagen_principal == "bolsa.svg"


def test_producto_bien_compuesto():
    compuesto = ProductoBien(
        tipo="bien",
        id=3001,
        nombre="Bolsa con Manija",
        descripcion="Receta fija",
        slug="bolsa-con-manija",
        imagen="compuesto.svg",
        cantidad_por_defecto=1000,
        atributos_posibles={},
        variaciones=[],
        visible=True,
        componentes=[
            ComponenteBien(
                tipo="variacion",
                referencia_id=1,
                cantidad=1,
                nombre="Bolsa base",
            ),
            ComponenteBien(
                tipo="servicio",
                referencia_id=2001,
                cantidad=1,
                nombre="Pegado",
            ),
        ],
    )
    assert compuesto.tipo == "bien"
    assert compuesto.es_compuesto
    assert compuesto.url_slug == "bolsa-con-manija"
    assert len(compuesto.componentes) == 2


def test_producto_servicio():
    servicio = ProductoServicio(
        tipo="servicio",
        id=2001,
        nombre="Pegado",
        descripcion="Pegado de manijas",
        slug="pegado",
        imagen="servicio.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["pegado"]),
    )
    assert servicio.tipo == "servicio"
    assert servicio.url_slug == "pegado"


def test_componente_bien_cantidad_invalida():
    with pytest.raises(ValidationError):
        ComponenteBien(
            tipo="variacion",
            referencia_id=1,
            cantidad=0,
            nombre="Bolsa base",
        )
