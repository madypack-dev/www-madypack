from typing import Callable

from dataclasses import dataclass
from typing import Protocol

from src.domain.commerce.cart import ArticuloCarrito, Carrito
from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import ProductoBien


class CasoUsoActualizarCarrito:
    def __init__(
        self,
        repositorio: IRepositorioCarrito,
        repositorio_catalogo: ICatalogRepository,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.repositorio = repositorio
        self.repositorio_catalogo = repositorio_catalogo
        self.registrar_error = registrar_error

    def ejecutar(self, actualizaciones: dict[int, int]) -> None:
        carrito = self.repositorio.obtener_carrito()
        modificado = False
        for id_articulo, nueva_cantidad in actualizaciones.items():
            moq = self._obtener_moq(id_articulo)
            if moq is None:
                self.registrar_error(f"Artículo inexistente {id_articulo} en actualización.")
                continue

            if nueva_cantidad < moq:
                self.registrar_error(
                    f"Cantidad {nueva_cantidad} inferior al MOQ ({moq}) para artículo {id_articulo}"
                )
                nueva_cantidad = moq

            try:
                if carrito.actualizar_cantidad(id_articulo, nueva_cantidad):
                    modificado = True
            except ValueError as err:
                self.registrar_error(f"Error de validación al actualizar artículo {id_articulo}: {err}")
                continue

        if modificado:
            self.repositorio.guardar_carrito(carrito)

    def _obtener_moq(self, id_articulo: int) -> int | None:
        res = self.repositorio_catalogo.obtener_variacion_por_id(id_articulo)
        if res:
            return res[1].cantidad_por_defecto

        producto = self.repositorio_catalogo.obtener_por_id(id_articulo)
        if isinstance(producto, ProductoBien):
            return producto.cantidad_por_defecto

        return None


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

    def ejecutar(
        self, producto_id: int, variacion_id: int | None, cantidad: int
    ) -> None:
        producto = self.repositorio_catalogo.obtener_por_id(producto_id)
        if producto is None:
            self.registrar_error(f"Intento de agregar producto inexistente: {producto_id}")
            raise ValueError("El producto no existe en el catálogo.")

        if isinstance(producto, ProductoBien):
            if producto.es_compuesto:
                self._agregar_compuesto(producto, cantidad)
            else:
                self._agregar_simple(producto, variacion_id, cantidad)
        else:
            self.registrar_error(f"Intento de agregar un servicio suelto: {producto_id}")
            raise ValueError("Los servicios solo pueden agregarse dentro de un producto compuesto.")

    def _agregar_simple(
        self, producto: ProductoBien, variacion_id: int | None, cantidad: int
    ) -> None:
        if variacion_id is None:
            self.registrar_error(f"Falta variación para producto simple {producto.id}")
            raise ValueError("Debe seleccionar una variación para este producto.")

        res = self.repositorio_catalogo.obtener_variacion_por_id(variacion_id)
        if not res or res[0].id != producto.id:
            self.registrar_error(
                f"La variación {variacion_id} no pertenece al producto {producto.id}"
            )
            raise ValueError("La variación seleccionada no es válida para este producto.")

        datos_variacion = res[1]

        if cantidad < datos_variacion.cantidad_por_defecto:
            self.registrar_error(
                f"Intento de agregar cantidad {cantidad} inferior al MOQ "
                f"({datos_variacion.cantidad_por_defecto}) para variante {variacion_id}"
            )
            raise ValueError(
                f"La cantidad mínima para este producto es de {datos_variacion.cantidad_por_defecto} unidades."
            )

        carrito = self.repositorio.obtener_carrito()

        try:
            atributos_str = " | ".join(
                f"{k.capitalize()}: {v}" for k, v in datos_variacion.atributos.items()
            )
            nombre = f"{producto.nombre} - {atributos_str}"
            gramaje = (
                "80 gr/m²"
                if "Sin Manija" in datos_variacion.atributos.values()
                else "100 gr/m²"
            )
            descripcion = f"Gramaje: {gramaje} | SKU: {datos_variacion.sku}"

            articulo = ArticuloCarrito(
                id=datos_variacion.id,
                nombre=nombre,
                descripcion=descripcion,
                cantidad=cantidad,
                imagen=datos_variacion.imagen,
                calculo=datos_variacion.calculo,
            )
            carrito.agregar_articulo(articulo)
            self.repositorio.guardar_carrito(carrito)
        except ValueError as err:
            self.registrar_error(f"Error de validación al agregar variación {variacion_id}: {err}")
            raise

    def _agregar_compuesto(self, producto: ProductoBien, cantidad: int) -> None:
        if cantidad < producto.cantidad_por_defecto:
            self.registrar_error(
                f"Intento de agregar cantidad {cantidad} inferior al MOQ "
                f"({producto.cantidad_por_defecto}) para compuesto {producto.id}"
            )
            raise ValueError(
                f"La cantidad mínima para este producto es de {producto.cantidad_por_defecto} unidades."
            )

        carrito = self.repositorio.obtener_carrito()

        try:
            componentes_str = " + ".join(c.nombre for c in producto.componentes)
            descripcion = f"Receta: {componentes_str}"

            articulo = ArticuloCarrito(
                id=producto.id,
                nombre=producto.nombre,
                descripcion=descripcion,
                cantidad=cantidad,
                imagen=producto.imagen,
                calculo=None,
            )
            carrito.agregar_articulo(articulo)
            self.repositorio.guardar_carrito(carrito)
        except ValueError as err:
            self.registrar_error(f"Error de validación al agregar compuesto {producto.id}: {err}")
            raise


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
