from typing import Callable

from src.domain.commerce.cart import ArticuloCarrito
from src.domain.commerce.catalog import ProductoVariable, VariacionProducto
from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository


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
            res = self.repositorio_catalogo.obtener_variacion_por_id(id_articulo)
            if not res:
                self.registrar_error(f"Variación inexistente {id_articulo} en actualización.")
                continue
            _, datos_variacion = res
            
            # Enforzar MOQ dinámico
            if nueva_cantidad < datos_variacion.cantidad_por_defecto:
                self.registrar_error(
                    f"Cantidad {nueva_cantidad} inferior al MOQ ({datos_variacion.cantidad_por_defecto}) para variante {id_articulo}"
                )
                nueva_cantidad = datos_variacion.cantidad_por_defecto

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
        res = self.repositorio_catalogo.obtener_variacion_por_id(id_articulo)
        if not res:
            self.registrar_error(f"Intento de agregar variación inexistente del catálogo: {id_articulo}")
            raise ValueError("El artículo no existe en el catálogo.")

        datos_producto, datos_variacion = res

        # Validar MOQ dinámico
        if cantidad < datos_variacion.cantidad_por_defecto:
            self.registrar_error(
                f"Intento de agregar cantidad {cantidad} inferior al MOQ ({datos_variacion.cantidad_por_defecto}) para variante {id_articulo}"
            )
            raise ValueError(f"La cantidad mínima para este producto es de {datos_variacion.cantidad_por_defecto} unidades.")

        carrito = self.repositorio.obtener_carrito()

        try:
            # Construir un nombre descriptivo combinando atributos
            atributos_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in datos_variacion.atributos.items())
            nombre = f"{datos_producto.nombre} - {atributos_str}"
            
            # El gramaje varía según el tipo de manija
            gramaje = "80 gr/m²" if "Sin Manija" in datos_variacion.atributos.values() else "100 gr/m²"
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
