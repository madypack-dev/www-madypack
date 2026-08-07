"""Caso de uso: generar el PDF de presupuesto a partir de líneas precalculadas."""

from datetime import date
from typing import Callable

from src.domain.quote.visual_identity import IdentidadVisual
from src.domain.quote.quote import (
    DatosSolicitante,
    LineaPresupuesto,
    Presupuesto,
)
from src.domain.quote.pdf_generator import IGeneradorDocumentoPresupuesto


class CasoUsoGenerarPresupuestoPDF:
    """Orquesta la generación de un presupuesto PDF a partir de líneas de presupuesto."""

    def __init__(
        self,
        generador_pdf: IGeneradorDocumentoPresupuesto,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.generador_pdf = generador_pdf
        self.registrar_error = registrar_error

    def ejecutar(
        self,
        datos_solicitante: DatosSolicitante,
        lineas: list[LineaPresupuesto],
        identidad_visual: IdentidadVisual,
        validez_dias: int,
        condiciones_comerciales: list[str],
    ) -> bytes:
        """Construye el agregado Presupuesto y delega la generación del PDF."""
        if not lineas:
            raise ValueError("El presupuesto debe contener al menos una línea de artículo.")

        total_estimado = sum(linea.subtotal for linea in lineas)

        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=validez_dias,
            datos_solicitante=datos_solicitante,
            lineas=lineas,
            condiciones_comerciales=condiciones_comerciales,
            total_estimado=total_estimado,
        )

        return self.generador_pdf.generar(presupuesto, identidad_visual)
