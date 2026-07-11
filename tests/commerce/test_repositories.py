import json
from unittest.mock import MagicMock
from src.adapters.commerce.cookie_repository import RepositorioCarritoCookie
from src.domain.commerce.cart import Carrito, ArticuloCarrito

def test_repositorio_carrito_cookie_vacio():
    cookies = {}
    repo = RepositorioCarritoCookie(cookies)
    carrito = repo.obtener_carrito()
    assert len(carrito.articulos) == 0

def test_repositorio_carrito_cookie_lista():
    datos = [
        {"id": 1, "nombre": "Bolsa A", "descripcion": "Desc A", "cantidad": 200, "imagen": "a.png"}
    ]
    cookies = {"articulos_carrito": json.dumps(datos)}
    repo = RepositorioCarritoCookie(cookies)
    carrito = repo.obtener_carrito()
    assert len(carrito.articulos) == 1
    assert carrito.articulos[0].id == 1
    assert carrito.articulos[0].cantidad == 200

def test_repositorio_carrito_cookie_diccionario():
    datos = {
        "articulos": [
            {"id": 2, "nombre": "Bolsa B", "descripcion": "Desc B", "cantidad": 300, "imagen": "b.png"}
        ]
    }
    cookies = {"articulos_carrito": json.dumps(datos)}
    repo = RepositorioCarritoCookie(cookies)
    carrito = repo.obtener_carrito()
    assert len(carrito.articulos) == 1
    assert carrito.articulos[0].id == 2
    assert carrito.articulos[0].cantidad == 300

def test_repositorio_carrito_cookie_invalido():
    cookies = {"articulos_carrito": "invalid-json"}
    registrar_error = MagicMock()
    repo = RepositorioCarritoCookie(cookies, registrar_error=registrar_error)
    carrito = repo.obtener_carrito()
    assert len(carrito.articulos) == 0
    registrar_error.assert_called_once()

def test_repositorio_carrito_cookie_otro_tipo():
    cookies = {"articulos_carrito": json.dumps("no-es-lista-ni-dicc")}
    repo = RepositorioCarritoCookie(cookies)
    carrito = repo.obtener_carrito()
    assert len(carrito.articulos) == 0

def test_repositorio_carrito_cookie_guardar():
    cookies = {}
    repo = RepositorioCarritoCookie(cookies)
    carrito = Carrito()
    art = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art)
    
    repo.guardar_carrito(carrito)
    serialized = repo.carrito_serializado
    assert serialized is not None
    
    datos = json.loads(serialized)
    assert len(datos["articulos"]) == 1
