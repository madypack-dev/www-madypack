"""Helpers de aplicación para el bounded context de presupuesto."""

from typing import Callable

from src.comercio.dominio.modelos.carrito import Carrito
from src.precios.adaptadores.servicios.cotizador import CotizadorServicio
from src.presupuesto.dominio.modelos.presupuesto import LineaPresupuesto


def construir_lineas_presupuesto(
    carrito: Carrito,
    cotizador: CotizadorServicio,
    registrar_error: Callable[[str], None] = lambda m: None,
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
            )
        )
    return lineas
