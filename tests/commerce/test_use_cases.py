import pytest
from unittest.mock import MagicMock

from src.application.commerce.cart_use_cases import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
)
from src.domain.commerce.cart import Carrito, ArticuloCarrito
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import ComponenteBien, ProductoBien


def _producto_bien_simple() -> ProductoBien:
    return ProductoBien(
        tipo="bien",
        id=1001,
        nombre="Bolsa A",
        descripcion="A",
        slug="bolsa-a",
        imagen="img.png",
        atributos_posibles={"color": ["Marrón"]},
        variaciones=[
            VariacionProducto(
                id=1,
                sku="B-SOS-M",
                atributos={"color": "Marrón"},
                imagen="img.png",
                cantidad_por_defecto=100,
                calculo=None,
                visible=True,
            )
        ],
        componentes=[],
        visible=True,
    )


def _producto_bien_compuesto() -> ProductoBien:
    return ProductoBien(
        tipo="bien",
        id=3001,
        nombre="Bolsa con Manija",
        descripcion="Compuesto",
        slug="bolsa-con-manija",
        imagen="bolsas-con-m.svg",
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
        ],
    )


def test_actualizar_carrito_caso_uso():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art1)

    repo.obtener_carrito.return_value = carrito

    prod = _producto_bien_simple()
    mock_catalog = MagicMock(spec=ICatalogRepository)
    mock_catalog.obtener_variacion_por_id.return_value = (prod, prod.variaciones[0])

    # Caso 1: actualización válida
    caso_uso = CasoUsoActualizarCarrito(repo, mock_catalog)
    caso_uso.ejecutar({1: 300})
    assert art1.cantidad == 300
    repo.guardar_carrito.assert_called_once_with(carrito)

    # Caso 2: error de validación en la actualización (cantidad inválida)
    repo.guardar_carrito.reset_mock()
    registrar_error = MagicMock()
    caso_uso_con_error = CasoUsoActualizarCarrito(repo, mock_catalog, registrar_error)
    caso_uso_con_error.ejecutar({1: 150})
    registrar_error.assert_called_once()
    repo.guardar_carrito.assert_not_called()


def test_agregar_al_carrito_caso_uso_simple():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    repo.obtener_carrito.return_value = carrito

    prod = _producto_bien_simple()
    mock_catalog = MagicMock(spec=ICatalogRepository)
    mock_catalog.obtener_por_id.side_effect = lambda pid: prod if pid == 1001 else None
    mock_catalog.obtener_variacion_por_id.return_value = (prod, prod.variaciones[0])

    caso_uso = CasoUsoAgregarAlCarrito(repo, mock_catalog)

    # Agregar variación válida
    caso_uso.ejecutar(producto_id=1001, variacion_id=1, cantidad=200)
    assert len(carrito.articulos) == 1
    assert carrito.articulos[0].id == 1
    assert carrito.articulos[0].cantidad == 200
    repo.guardar_carrito.assert_called_once_with(carrito)

    # Agregar producto inexistente en catálogo
    repo.guardar_carrito.reset_mock()
    registrar_error = MagicMock()
    caso_uso_con_error = CasoUsoAgregarAlCarrito(repo, mock_catalog, registrar_error)
    with pytest.raises(ValueError) as exc_info:
        caso_uso_con_error.ejecutar(producto_id=99, variacion_id=1, cantidad=200)
    assert "El producto no existe en el catálogo." in str(exc_info.value)
    registrar_error.assert_called_once()
    repo.guardar_carrito.assert_not_called()

    # Agregar cantidad inválida
    registrar_error.reset_mock()
    with pytest.raises(ValueError):
        caso_uso_con_error.ejecutar(producto_id=1001, variacion_id=1, cantidad=150)
    registrar_error.assert_called_once()


def test_agregar_al_carrito_caso_uso_compuesto():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    repo.obtener_carrito.return_value = carrito

    prod = _producto_bien_compuesto()
    mock_catalog = MagicMock(spec=ICatalogRepository)
    mock_catalog.obtener_por_id.return_value = prod

    caso_uso = CasoUsoAgregarAlCarrito(repo, mock_catalog)
    caso_uso.ejecutar(producto_id=3001, variacion_id=None, cantidad=2000)

    assert len(carrito.articulos) == 1
    assert carrito.articulos[0].id == 3001
    assert carrito.articulos[0].cantidad == 2000
    assert carrito.articulos[0].calculo is None
    repo.guardar_carrito.assert_called_once_with(carrito)


def test_eliminar_del_carrito_caso_uso():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art1)
    repo.obtener_carrito.return_value = carrito

    caso_uso = CasoUsoEliminarDelCarrito(repo)

    # Eliminar artículo existente
    caso_uso.ejecutar(id_articulo=1)
    assert len(carrito.articulos) == 0
    repo.guardar_carrito.assert_called_once_with(carrito)

    # Eliminar artículo inexistente
    repo.guardar_carrito.reset_mock()
    registrar_error = MagicMock()
    caso_uso_con_error = CasoUsoEliminarDelCarrito(repo, registrar_error)
    with pytest.raises(ValueError) as exc_info:
        caso_uso_con_error.ejecutar(id_articulo=99)
    assert "El artículo no está en el carrito." in str(exc_info.value)
    registrar_error.assert_called_once()
    repo.guardar_carrito.assert_not_called()


def test_obtener_resumen_carrito_caso_uso():
    from src.application.commerce.cart_use_cases import CasoUsoObtenerResumenCarrito, ICotizador

    # Mockear cotizador
    cotizador = MagicMock(spec=ICotizador)
    cotizador.calcular_precio_estimado.side_effect = lambda art: 1500.0 if art.id == 1 else 2500.0

    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    art2 = ArticuloCarrito(id=2, nombre="Bolsa B", descripcion="B", cantidad=200, imagen="img.png")
    carrito.agregar_articulo(art1)
    carrito.agregar_articulo(art2)

    caso_uso = CasoUsoObtenerResumenCarrito()
    resumen = caso_uso.ejecutar(carrito, cotizador)

    assert resumen.articulos == [art1, art2]
    assert resumen.total_bolsas == 300
    assert resumen.precio_total == 4000.0


def test_obtener_resumen_carrito_vacio():
    from src.application.commerce.cart_use_cases import CasoUsoObtenerResumenCarrito, ICotizador

    cotizador = MagicMock(spec=ICotizador)
    carrito = Carrito()

    caso_uso = CasoUsoObtenerResumenCarrito()
    resumen = caso_uso.ejecutar(carrito, cotizador)

    assert resumen.articulos == []
    assert resumen.total_bolsas == 0
    assert resumen.precio_total == 0.0


def test_obtener_resumen_carrito_con_error_cotizador():
    from src.application.commerce.cart_use_cases import CasoUsoObtenerResumenCarrito, ICotizador

    cotizador = MagicMock(spec=ICotizador)
    cotizador.calcular_precio_estimado.side_effect = Exception("Falla de cotización")

    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art1)

    registrar_error = MagicMock()
    caso_uso = CasoUsoObtenerResumenCarrito(registrar_error=registrar_error)
    resumen = caso_uso.ejecutar(carrito, cotizador)

    assert resumen.articulos == [art1]
    assert resumen.total_bolsas == 100
    assert resumen.precio_total == 0.0
    registrar_error.assert_called_once()
