"""Caso de uso: procesar una solicitud de presupuesto (con o sin carrito)."""

import uuid
from collections.abc import Callable

from src.comercio.dominio.modelos.carrito import Carrito
from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest
from src.lead.dominio.modelos.lead import Lead
from src.lead.dominio.puertos.repositorio import ILeadRepository
from src.presupuesto.dominio.puertos.registro_fallback import IRegistroFallbackLead


class ProcesarSolicitudPresupuesto:
    """Orquesta el procesamiento completo de una solicitud de presupuesto."""

    def __init__(
        self,
        repositorio: ILeadRepository,
        chatwoot_inbox_id: int,
        registro_fallback: IRegistroFallbackLead,
        registrar_error: Callable[[str], None] = lambda m: None,
    ):
        self.repositorio = repositorio
        self.chatwoot_inbox_id = chatwoot_inbox_id
        self.registro_fallback = registro_fallback
        self.registrar_error = registrar_error

    async def ejecutar(
        self,
        request: CrearLeadRequest,
        carrito: Carrito,
    ) -> Lead:
        if carrito.articulos:
            return await self._procesar_con_carrito(request)
        return await self._procesar_cotizacion_general(request)

    async def _procesar_con_carrito(self, request: CrearLeadRequest) -> Lead:
        lead = Lead.crear(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email,
        )
        await self._guardar_lead(lead)
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
