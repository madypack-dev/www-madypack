"""Presentador de la confirmación de presupuesto.

No depende de infraestructura ni de librerías externas.
Convierte entidades de dominio en un objeto listo para ser renderizado.
"""

import urllib.parse
from dataclasses import dataclass

from src.domain.commerce.cart import Carrito
from src.domain.lead.lead import Lead


@dataclass(frozen=True)
class ConfirmacionPresupuestoPresentada:
    """DTO de presentación para la vista de confirmación de presupuesto."""

    lead_id: str
    codigo_referencia: str
    whatsapp_url: str
    pdf_url: str | None


class PresentadorConfirmacionPresupuesto:
    """Construye la respuesta de confirmación a partir de entidades puras."""

    def __init__(self, whatsapp_phone: str):
        self.whatsapp_phone = whatsapp_phone

    def presentar(
        self,
        lead: Lead,
        carrito: Carrito,
        mensaje: str | None = None,
    ) -> ConfirmacionPresupuestoPresentada:
        """Presenta la confirmación de una cotización con o sin carrito."""
        incluir_pdf = bool(carrito.articulos)
        cuerpo = self._construir_mensaje(lead, carrito, mensaje)
        whatsapp_url = self._construir_whatsapp_url(cuerpo)
        pdf_url = self._construir_pdf_url(lead) if incluir_pdf else None

        return ConfirmacionPresupuestoPresentada(
            lead_id=lead.id or "",
            codigo_referencia=lead.codigo_referencia,
            whatsapp_url=whatsapp_url,
            pdf_url=pdf_url,
        )

    def presentar_emergencia(
        self,
        lead: Lead,
        ref_code: str,
    ) -> ConfirmacionPresupuestoPresentada:
        """Presenta la confirmación de emergencia ante una falla crítica."""
        cuerpo = (
            f"Hola, mi nombre es {lead.nombre} de la empresa *{lead.empresa}*. "
            f"Ocurrió un inconveniente al generar la cotización online ({ref_code}). "
            f"Quisiera coordinar la cotización comercial directamente por acá."
        )
        return ConfirmacionPresupuestoPresentada(
            lead_id=lead.id or "",
            codigo_referencia=ref_code,
            whatsapp_url=self._construir_whatsapp_url(cuerpo),
            pdf_url=self._construir_pdf_url(lead),
        )

    def _construir_mensaje(
        self,
        lead: Lead,
        carrito: Carrito,
        mensaje: str | None,
    ) -> str:
        if carrito.articulos:
            detalles = []
            for art in carrito.articulos:
                unidad = getattr(art, "unidad", "u.")
                detalles.append(f"- {art.cantidad:,} {unidad} de {art.nombre} ({art.descripcion})")
            detalles_str = "\n".join(detalles)
            return (
                f"Hola, me contacto de parte de la empresa *{lead.empresa}* "
                f"(mi nombre es {lead.nombre}) referente a la cotización *{lead.codigo_referencia}*.\n\n"
                f"Detalle de mi solicitud:\n{detalles_str}\n\n"
                f"Quisiera coordinar el presupuesto formal y los detalles de entrega."
            )
        return (
            f"Hola, me contacto de parte de la empresa *{lead.empresa}* "
            f"(mi nombre es {lead.nombre}) por la solicitud de cotización *{lead.codigo_referencia}*.\n\n"
            f"{mensaje or 'Quiero cotizar bolsas de papel.'}"
        )

    def _construir_whatsapp_url(self, cuerpo: str) -> str:
        return f"https://wa.me/{self.whatsapp_phone}?text={urllib.parse.quote(cuerpo)}"

    def _construir_pdf_url(self, lead: Lead) -> str:
        query_params = urllib.parse.urlencode(
            {
                "ref": lead.codigo_referencia,
            }
        )
        return f"/presupuesto/descargar/?{query_params}"
