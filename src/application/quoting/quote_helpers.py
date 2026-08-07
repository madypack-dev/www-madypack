"""Helpers de aplicación para el bounded context de presupuesto."""

from typing import Callable, Protocol

from src.domain.commerce.cart import Carrito, ArticuloCarrito
from src.domain.quote.quote import LineaPresupuesto


class ICotizador(Protocol):
    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        ...


def construir_lineas_presupuesto(
    carrito: Carrito,
    cotizador: ICotizador,
    registrar_error: Callable[[str], None] = lambda _: None,
) -> list[LineaPresupuesto]:
    """Construye las líneas de presupuesto a partir de los artículos del carrito."""
    lineas: list[LineaPresupuesto] = []
    for articulo in carrito.articulos:
        try:
            subtotal = cotizador.calcular_precio_estimado(articulo)
        except Exception as err:
            registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            subtotal = 0.0

        precio_unitario = (
            subtotal / articulo.cantidad if articulo.cantidad > 0 else 0.0
        )
        lineas.append(
            LineaPresupuesto(
                id_articulo=articulo.id,
                nombre=articulo.nombre,
                descripcion=articulo.descripcion,
                cantidad=articulo.cantidad,
                precio_unitario_estimado=precio_unitario,
                subtotal=subtotal,
                unidad=articulo.unidad,
            )
        )
    return lineas

