from typing import Callable
from src.comercio.dominio.puertos.repositorio import IRepositorioCarrito
from src.comercio.dominio.modelos.carrito import ArticuloCarrito
from src.infraestructura.datos.modelos import ArticuloCatalogo

class CasoUsoActualizarCarrito:
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda m: None):
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
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda m: None):
        self.repositorio = repositorio
        self.registrar_error = registrar_error

    def ejecutar(self, id_articulo: int, cantidad: int, catalogo: list[ArticuloCatalogo]) -> None:
        datos_producto = next((p for p in catalogo if p.id == id_articulo), None)
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
                imagen=datos_producto.imagen
            )
            carrito.agregar_articulo(articulo)
            self.repositorio.guardar_carrito(carrito)
        except ValueError as err:
            self.registrar_error(f"Error de validación al agregar artículo {id_articulo} al carrito: {err}")
            raise err
