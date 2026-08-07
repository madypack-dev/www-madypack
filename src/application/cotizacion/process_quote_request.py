"""Caso de uso: procesar una solicitud de presupuesto (con o sin carrito)."""

import uuid
from collections.abc import Callable
from datetime import date

from src.application.cotizacion.quote_helpers import ICotizador, construir_lineas_presupuesto
from src.application.lead.lead_dtos import CrearLeadRequest
from src.domain.comercio.cart import Carrito
from src.domain.cotizacion.fallback_registry import IRegistroFallbackLead
from src.domain.cotizacion.quote import DatosSolicitante, Presupuesto
from src.domain.cotizacion.quote_repository import IQuoteRepository
from src.domain.lead.lead import Lead
from src.domain.lead.lead_repository import ILeadRepository


class ProcesarSolicitudPresupuesto:
    """Orquesta el procesamiento completo de una solicitud de presupuesto."""

    def __init__(
        self,
        repositorio: ILeadRepository,
        chatwoot_inbox_id: int,
        registro_fallback: IRegistroFallbackLead,
        quote_repository: IQuoteRepository,
        cotizador: ICotizador,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.repositorio = repositorio
        self.chatwoot_inbox_id = chatwoot_inbox_id
        self.registro_fallback = registro_fallback
        self.quote_repository = quote_repository
        self.cotizador = cotizador
        self.registrar_error = registrar_error

    async def ejecutar(
        self,
        request: CrearLeadRequest,
        carrito: Carrito,
        validez_dias: int = 15,
        condiciones_comerciales: list[str] | None = None,
    ) -> Lead:
        condiciones = condiciones_comerciales or []
        if carrito.articulos:
            return await self._procesar_con_carrito(request, carrito, validez_dias, condiciones)
        return await self._procesar_cotizacion_general(request)

    async def _procesar_con_carrito(
        self,
        request: CrearLeadRequest,
        carrito: Carrito,
        validez_dias: int,
        condiciones_comerciales: list[str],
    ) -> Lead:
        lead = Lead.crear(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email,
        )
        await self._guardar_lead(lead)

        try:
            lineas = construir_lineas_presupuesto(carrito, self.cotizador, self.registrar_error)
            total_estimado = sum(linea.subtotal for linea in lineas)
            presupuesto = Presupuesto(
                fecha_emision=date.today(),
                validez_dias=validez_dias,
                datos_solicitante=DatosSolicitante(
                    nombre=request.nombre,
                    email=request.email,
                    telefono=request.telefono,
                    empresa=request.empresa,
                ),
                lineas=lineas,
                condiciones_comerciales=condiciones_comerciales,
                total_estimado=total_estimado,
            )
            self.quote_repository.guardar(lead.codigo_referencia, presupuesto)
        except Exception as err:
            self.registrar_error(
                f"Error al guardar presupuesto local para ref {lead.codigo_referencia}: {err}"
            )

        return lead

    async def _procesar_cotizacion_general(self, request: CrearLeadRequest) -> Lead:
        lead = Lead.crear_cotizacion_general(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email,
        )
        await self._guardar_lead(lead)
        return lead

    async def _guardar_lead(self, lead: Lead) -> None:
        try:
            lead_id = await self.repositorio.guardar(lead, self.chatwoot_inbox_id)
            lead.id = lead_id
        except Exception as err:
            self.registrar_error(f"Error de integración con Chatwoot: {err}")
            lead.id = f"FALLBACK-{uuid.uuid4()}"
            self.registro_fallback.guardar(lead, str(err))
