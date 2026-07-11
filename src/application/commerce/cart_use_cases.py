from typing import Callable

from src.domain.commerce.cart import ArticuloCarrito
from src.domain.commerce.catalog import ArticuloCatalogo
from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository


class CasoUsoActualizarCarrito:
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda _: None):
        self.repositorio = repositorio
        self.registrar_error = registrar_error

    def ejecutar(self, actualizaciones: dict[int, int]) -> None:
        carrito = self.repositorio.obtener_carrito()
        modificado = False
        for id_articulo, nueva_cantidad in actualizaciones.items():
            try:
                if carrito.actualizar_cantidad(id_articulo, nueva_cantidad):
                    modificado = True
            except ValueError as err:
                self.registrar_error(f"Error de validación al actualizar artículo {id_articulo}: {err}")
                continue
        if modificado:
            self.repositorio.guardar_carrito(carrito)


class CasoUsoAgregarAlCarrito:
    def __init__(
        self,
        repositorio: IRepositorioCarrito,
        repositorio_catalogo: ICatalogRepository,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.repositorio = repositorio
        self.repositorio_catalogo = repositorio_catalogo
        self.registrar_error = registrar_error

    def ejecutar(self, id_articulo: int, cantidad: int) -> None:
        datos_producto = self.repositorio_catalogo.obtener_por_id(id_articulo)
        if not datos_producto:
            self.registrar_error(f"Intento de agregar artículo inexistente del catálogo: {id_articulo}")
            raise ValueError("El artículo no existe en el catálogo.")

        carrito = self.repositorio.obtener_carrito()

        try:
            articulo = ArticuloCarrito(
                id=datos_producto.id,
                nombre=datos_producto.nombre,
                descripcion=datos_producto.descripcion,
                cantidad=cantidad,
                imagen=datos_producto.imagen,
                calculo=datos_producto.calculo,
            )
            carrito.agregar_articulo(articulo)
            self.repositorio.guardar_carrito(carrito)
        except ValueError as err:
            self.registrar_error(f"Error de validación al agregar artículo {id_articulo} al carrito: {err}")
            raise err


class CasoUsoEliminarDelCarrito:
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda _: None):
        self.repositorio = repositorio
        self.registrar_error = registrar_error

    def ejecutar(self, id_articulo: int) -> None:
        carrito = self.repositorio.obtener_carrito()

        if not carrito.eliminar_articulo(id_articulo):
            self.registrar_error(f"Intento de eliminar artículo que no está en el carrito: {id_articulo}")
            raise ValueError("El artículo no está en el carrito.")

        self.repositorio.guardar_carrito(carrito)


from dataclasses import dataclass
from typing import Protocol
from src.domain.commerce.cart import Carrito


class ICotizador(Protocol):
    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        ...


@dataclass(frozen=True)
class ResumenCarritoDTO:
    articulos: list[ArticuloCarrito]
    total_bolsas: int
    precio_total: float


class CasoUsoObtenerResumenCarrito:
    def __init__(self, registrar_error: Callable[[str], None] = lambda _: None):
        self.registrar_error = registrar_error

    def ejecutar(self, carrito: Carrito, cotizador: ICotizador) -> ResumenCarritoDTO:
        precio_total = 0.0
        for articulo in carrito.articulos:
            try:
                precio_total += cotizador.calcular_precio_estimado(articulo)
            except Exception as err:
                self.registrar_error(f"No se pudo cotizar artículo {articulo.id}: {err}")

        return ResumenCarritoDTO(
            articulos=carrito.articulos,
            total_bolsas=carrito.total_bolsas,
            precio_total=precio_total,
        )
