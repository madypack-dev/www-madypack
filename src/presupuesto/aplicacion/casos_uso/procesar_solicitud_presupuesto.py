"""Caso de uso: procesar una solicitud de presupuesto (con o sin carrito)."""

import json
import os
import urllib.parse
import uuid
from datetime import datetime
from typing import Callable

from src.comercio.dominio.modelos.carrito import Carrito
from src.lead.aplicacion.dtos.lead_dtos import (
    CrearLeadRequest,
    ConfirmacionPresupuestoResponse,
)
from src.lead.dominio.modelos.lead import Lead
from src.lead.dominio.puertos.repositorio import ILeadRepository


class ProcesarSolicitudPresupuesto:
    """Orquesta el procesamiento completo de una solicitud de presupuesto."""

    def __init__(
        self,
        repositorio: ILeadRepository,
        chatwoot_inbox_id: int,
        whatsapp_phone: str,
        registrar_error: Callable[[str], None] = lambda m: None,
        fallback_file_path: str = "logs/failed_leads.log",
    ):
        self.repositorio = repositorio
        self.chatwoot_inbox_id = chatwoot_inbox_id
        self.whatsapp_phone = whatsapp_phone
        self.registrar_error = registrar_error
        self.fallback_file_path = fallback_file_path

    async def ejecutar(
        self,
        request: CrearLeadRequest,
        carrito: Carrito,
        mensaje: str | None = None,
    ) -> ConfirmacionPresupuestoResponse:
        try:
            if carrito.articulos:
                return await self._procesar_con_carrito(request, carrito, mensaje)
            return await self._procesar_cotizacion_general(request, mensaje)
        except Exception as err:
            self.registrar_error(f"Falla crítica inesperada procesando presupuesto: {err}")
            return self._respuesta_emergencia(request, err)

    async def _procesar_con_carrito(
        self,
        request: CrearLeadRequest,
        carrito: Carrito,
        mensaje: str | None,
    ) -> ConfirmacionPresupuestoResponse:
        lead = Lead.crear(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email,
        )
        await self._guardar_lead(lead)
        return self._construir_respuesta(lead, carrito.total_lineas, mensaje, incluir_pdf=True)

    async def _procesar_cotizacion_general(
        self,
        request: CrearLeadRequest,
        mensaje: str | None,
    ) -> ConfirmacionPresupuestoResponse:
        lead = Lead.crear(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email,
        )
        lead.codigo_referencia = lead.codigo_referencia.replace("COT-", "COT-GEN-")
        await self._guardar_lead(lead)
        return self._construir_respuesta(lead, 0, mensaje, incluir_pdf=False)

    async def _guardar_lead(self, lead: Lead) -> None:
        try:
            lead_id = await self.repositorio.guardar(lead, self.chatwoot_inbox_id)
            lead.id = lead_id
        except Exception as err:
            self.registrar_error(f"Error de integración con Chatwoot: {err}")
            lead.id = f"FALLBACK-{uuid.uuid4()}"
            self._guardar_fallback_local(lead, str(err))

    def _construir_respuesta(
        self,
        lead: Lead,
        total_lineas: int,
        mensaje: str | None,
        incluir_pdf: bool,
    ) -> ConfirmacionPresupuestoResponse:
        if total_lineas > 0:
            cuerpo = (
                f"Hola, me contacto de parte de la empresa *{lead.empresa}* "
                f"(mi nombre es {lead.nombre}) referente a la cotización *{lead.codigo_referencia}*.\n\n"
                f"Tengo un total de *{total_lineas}* producto(s) en mi lista de cotización.\n\n"
                f"Quisiera coordinar el presupuesto formal y los detalles de entrega."
            )
        else:
            cuerpo = (
                f"Hola, me contacto de parte de la empresa *{lead.empresa}* "
                f"(mi nombre es {lead.nombre}) por la solicitud de cotización *{lead.codigo_referencia}*.\n\n"
                f"{mensaje or 'Quiero cotizar bolsas de papel.'}"
            )

        whatsapp_url = (
            f"https://wa.me/{self.whatsapp_phone}?text={urllib.parse.quote(cuerpo)}"
        )
        pdf_url = self._construir_pdf_url(lead) if incluir_pdf else None

        return ConfirmacionPresupuestoResponse(
            lead_id=lead.id,
            codigo_referencia=lead.codigo_referencia,
            whatsapp_url=whatsapp_url,
            pdf_url=pdf_url,
        )

    def _construir_pdf_url(self, lead: Lead) -> str:
        query_params = urllib.parse.urlencode(
            {
                "ref": lead.codigo_referencia,
                "name": lead.nombre,
                "company": lead.empresa,
                "email": str(lead.email),
                "phone": lead.telefono,
            }
        )
        return f"/presupuesto/descargar/?{query_params}"

    def _respuesta_emergencia(
        self,
        request: CrearLeadRequest,
        error: Exception,
    ) -> ConfirmacionPresupuestoResponse:
        ref_code = f"COT-ERR-{str(uuid.uuid4())[:8].upper()}"

        try:
            fallback_data = {
                "timestamp": datetime.now().isoformat(),
                "lead_id": f"INFRA-ERR-{uuid.uuid4()}",
                "codigo_referencia": ref_code,
                "nombre": request.nombre,
                "empresa": request.empresa,
                "email": str(request.email),
                "telefono": request.telefono,
                "error": f"Falla crítica de infraestructura: {str(error)}",
            }
            os.makedirs("logs", exist_ok=True)
            with open(self.fallback_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(fallback_data) + "\n")
        except Exception as file_err:
            self.registrar_error(f"No se pudo guardar el lead de emergencia: {file_err}")

        cuerpo = (
            f"Hola, mi nombre es {request.nombre} de la empresa *{request.empresa}*. "
            f"Ocurrió un inconveniente al generar la cotización online ({ref_code}). "
            f"Quisiera coordinar la cotización comercial directamente por acá."
        )
        whatsapp_url = (
            f"https://wa.me/{self.whatsapp_phone}?text={urllib.parse.quote(cuerpo)}"
        )
        pdf_url = f"/presupuesto/descargar/?{urllib.parse.urlencode({
            'ref': ref_code,
            'name': request.nombre,
            'company': request.empresa,
            'email': str(request.email),
            'phone': request.telefono,
        })}"

        return ConfirmacionPresupuestoResponse(
            lead_id=f"ERR-{uuid.uuid4()}",
            codigo_referencia=ref_code,
            whatsapp_url=whatsapp_url,
            pdf_url=pdf_url,
        )

    def _guardar_fallback_local(self, lead: Lead, error_msg: str) -> None:
        fallback_data = {
            "timestamp": datetime.now().isoformat(),
            "lead_id": lead.id,
            "codigo_referencia": lead.codigo_referencia,
            "nombre": lead.nombre,
            "empresa": lead.empresa,
            "email": str(lead.email),
            "telefono": lead.telefono,
            "error": error_msg,
        }
        try:
            dir_name = os.path.dirname(self.fallback_file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(self.fallback_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(fallback_data) + "\n")
        except Exception as file_err:
            self.registrar_error(
                f"No se pudo guardar el lead en el archivo de contingencia local: {file_err}"
            )
