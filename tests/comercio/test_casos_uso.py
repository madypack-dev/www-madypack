import pytest
from unittest.mock import MagicMock
from src.comercio.aplicacion.casos_uso.carrito import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
)
from src.comercio.dominio.modelos.carrito import Carrito, ArticuloCarrito
from src.comercio.dominio.modelos.catalogo import ArticuloCatalogo
from src.comercio.dominio.puertos.repositorio import IRepositorioCarrito

def test_actualizar_carrito_caso_uso():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art1)
    
    repo.obtener_carrito.return_value = carrito
    
    # Caso 1: actualización válida
    caso_uso = CasoUsoActualizarCarrito(repo)
    caso_uso.ejecutar({1: 300})
    assert art1.cantidad == 300
    repo.guardar_carrito.assert_called_once_with(carrito)

    # Caso 2: error de validación en la actualización (cantidad inválida)
    repo.guardar_carrito.reset_mock()
    registrar_error = MagicMock()
    caso_uso_con_error = CasoUsoActualizarCarrito(repo, registrar_error)
    # Mockear actualizar_cantidad para lanzar ValueError (bypasseando setattr de Pydantic)
    object.__setattr__(carrito, "actualizar_cantidad", MagicMock(side_effect=ValueError("La cantidad debe ser múltiplo de 100.")))
    caso_uso_con_error.ejecutar({1: 150})
    registrar_error.assert_called_once()
    repo.guardar_carrito.assert_not_called()

def test_agregar_al_carrito_caso_uso():
    repo = MagicMock(spec=IRepositorioCarrito)
    carrito = Carrito()
    repo.obtener_carrito.return_value = carrito
    
    catalogo = [
        ArticuloCatalogo(id=1, nombre="Bolsa A", descripcion="A", cantidad_por_defecto=100, imagen="img.png"),
    ]
    
    caso_uso = CasoUsoAgregarAlCarrito(repo)
    
    # Agregar artículo válido
    caso_uso.ejecutar(id_articulo=1, cantidad=200, catalogo=catalogo)
    assert len(carrito.articulos) == 1
    assert carrito.articulos[0].id == 1
    assert carrito.articulos[0].cantidad == 200
    repo.guardar_carrito.assert_called_once_with(carrito)
    
    # Agregar artículo inexistente en catálogo
    repo.guardar_carrito.reset_mock()
    registrar_error = MagicMock()
    caso_uso_con_error = CasoUsoAgregarAlCarrito(repo, registrar_error)
    with pytest.raises(ValueError) as exc_info:
        caso_uso_con_error.ejecutar(id_articulo=99, cantidad=200, catalogo=catalogo)
    assert "El artículo no existe en el catálogo." in str(exc_info.value)
    registrar_error.assert_called_once()
    repo.guardar_carrito.assert_not_called()

    # Agregar cantidad inválida
    registrar_error.reset_mock()
    with pytest.raises(ValueError):
        caso_uso_con_error.ejecutar(id_articulo=1, cantidad=150, catalogo=catalogo)
    registrar_error.assert_called_once()

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
    from src.comercio.aplicacion.casos_uso.carrito import CasoUsoObtenerResumenCarrito, ICotizador
    
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
    assert resumen.total_bolsas_formateado == "300 unidades"
    assert resumen.precio_estimado_formateado == "$ 4.000,00"


def test_obtener_resumen_carrito_vacio():
    from src.comercio.aplicacion.casos_uso.carrito import CasoUsoObtenerResumenCarrito, ICotizador
    
    cotizador = MagicMock(spec=ICotizador)
    carrito = Carrito()
    
    caso_uso = CasoUsoObtenerResumenCarrito()
    resumen = caso_uso.ejecutar(carrito, cotizador)
    
    assert resumen.articulos == []
    assert resumen.total_bolsas_formateado == "0 unidades"
    assert resumen.precio_estimado_formateado == "A cotizar"


def test_obtener_resumen_carrito_con_error_cotizador():
    from src.comercio.aplicacion.casos_uso.carrito import CasoUsoObtenerResumenCarrito, ICotizador
    
    cotizador = MagicMock(spec=ICotizador)
    cotizador.calcular_precio_estimado.side_effect = Exception("Falla de cotización")
    
    carrito = Carrito()
    art1 = ArticuloCarrito(id=1, nombre="Bolsa A", descripcion="A", cantidad=100, imagen="img.png")
    carrito.agregar_articulo(art1)
    
    registrar_error = MagicMock()
    caso_uso = CasoUsoObtenerResumenCarrito(registrar_error=registrar_error)
    resumen = caso_uso.ejecutar(carrito, cotizador)
    
    assert resumen.articulos == [art1]
    assert resumen.total_bolsas_formateado == "100 unidades"
    assert resumen.precio_estimado_formateado == "A cotizar"
    registrar_error.assert_called_once()

