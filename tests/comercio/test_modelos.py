import pytest
from pydantic import ValidationError
from src.domain.comercio.modelos.carrito import Carrito, ArticuloCarrito, CalculoArticulo

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
