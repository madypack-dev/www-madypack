"""Caso de uso: generar el PDF de presupuesto a partir del carrito actual."""

from datetime import date
from typing import Callable

from src.comercio.dominio.puertos.repositorio import IRepositorioCarrito
from src.comercio.dominio.puertos.servicio_precios import IServicioPrecios
from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import (
    DatosSolicitante,
    LineaPresupuesto,
    Presupuesto,
)
from src.presupuesto.dominio.puertos.generador_pdf import IGeneradorDocumentoPresupuesto


class CasoUsoGenerarPresupuestoPDF:
    """Orquesta la generación de un presupuesto PDF desde el carrito del usuario."""

    def __init__(
        self,
        repositorio_carrito: IRepositorioCarrito,
        servicio_precios: IServicioPrecios,
        generador_pdf: IGeneradorDocumentoPresupuesto,
        registrar_error: Callable[[str], None] = lambda m: None,
    ):
        self.repositorio_carrito = repositorio_carrito
        self.servicio_precios = servicio_precios
        self.generador_pdf = generador_pdf
        self.registrar_error = registrar_error

    def ejecutar(
        self,
        datos_solicitante: DatosSolicitante,
        identidad_visual: IdentidadVisual,
        validez_dias: int,
        condiciones_comerciales: list[str],
    ) -> bytes:
        """Construye el agregado Presupuesto y delega la generación del PDF."""
        carrito = self.repositorio_carrito.obtener_carrito()
        if not carrito.articulos:
            raise ValueError("El carrito está vacío. No se puede generar un presupuesto sin artículos.")

        lineas: list[LineaPresupuesto] = []
        total_estimado = 0.0

        for articulo in carrito.articulos:
            try:
                subtotal = self.servicio_precios.calcular_precio_estimado(
                    articulo.id, articulo.cantidad
                )
            except Exception as err:
                self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
                subtotal = 0.0

            precio_unitario_estimado = (
                subtotal / articulo.cantidad if articulo.cantidad > 0 else 0.0
            )

            lineas.append(
                LineaPresupuesto(
                    id_articulo=articulo.id,
                    nombre=articulo.nombre,
                    descripcion=articulo.descripcion,
                    cantidad=articulo.cantidad,
                    precio_unitario_estimado=precio_unitario_estimado,
                    subtotal=subtotal,
                )
            )
            total_estimado += subtotal

        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=validez_dias,
            datos_solicitante=datos_solicitante,
            lineas=lineas,
            condiciones_comerciales=condiciones_comerciales,
            total_estimado=total_estimado,
        )

        return self.generador_pdf.generar(presupuesto, identidad_visual)
