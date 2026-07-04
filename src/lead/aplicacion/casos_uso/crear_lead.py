import uuid
import urllib.parse
from datetime import datetime
from typing import Callable

from src.comercio.dominio.modelos.carrito import Carrito
from src.lead.dominio.modelos.lead import Lead
from src.lead.dominio.modelos.eventos import LeadCreado
from src.lead.dominio.puertos.repositorio import ILeadRepository
from src.lead.dominio.puertos.publicador_eventos import IPublicadorEventos
from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest, ConfirmacionPresupuestoResponse

class CrearLeadDesdePresupuesto:
    """Orquestador de negocio para la captura del lead."""
    
    def __init__(
        self,
        repositorio: ILeadRepository,
        publicador_eventos: IPublicadorEventos,
        chatwoot_inbox_id: int,
        whatsapp_phone: str,
        registrar_error: Callable[[str], None] = lambda m: None
    ):
        self.repositorio = repositorio
        self.publicador_eventos = publicador_eventos
        self.chatwoot_inbox_id = chatwoot_inbox_id
        self.whatsapp_phone = whatsapp_phone
        self.registrar_error = registrar_error

    async def ejecutar(self, request: CrearLeadRequest, carrito: Carrito) -> ConfirmacionPresupuestoResponse:
        """
        Flujo de Negocio:
        1. Instancia y genera el Lead (entidad de dominio).
        2. Intenta persistir el contacto en Chatwoot a través del puerto.
        3. En caso de falla de Chatwoot, captura la excepción y continúa usando un ID temporal.
        4. Construye y dispara el evento de dominio LeadCreado.
        5. Formatea el mensaje para WhatsApp (wa.me) con el conteo de líneas.
        6. Retorna los enlaces correspondientes para la vista de confirmación.
        """
        # 1. Crear entidad del dominio (genera el código de referencia único COT-...)
        lead = Lead.crear(
            nombre=request.nombre,
            empresa=request.empresa,
            telefono=request.telefono,
            email=request.email
        )
        
        # 2. Persistir en Chatwoot
        try:
            lead_id = await self.repositorio.guardar(lead, self.chatwoot_inbox_id)
            lead.id = lead_id
        except Exception as err:
            self.registrar_error(f"Error de integración con Chatwoot: {err}")
            # Fallback: ID temporal
            lead.id = f"FALLBACK-{uuid.uuid4()}"

        # 3. Emitir evento de dominio
        resumen_lineas = carrito.total_lineas
        evento = LeadCreado(
            id_evento=uuid.uuid4(),
            ocurrido_en=datetime.now(),
            lead_id=lead.id,
            nombre=lead.nombre,
            empresa=lead.empresa,
            telefono=lead.telefono,
            email=lead.email,
            codigo_referencia=lead.codigo_referencia,
            resumen_lineas=resumen_lineas
        )
        try:
            await self.publicador_eventos.publicar_lead_creado(evento)
        except Exception as event_err:
            self.registrar_error(f"Error publicando evento LeadCreado: {event_err}")

        # 4. Formatear mensaje para WhatsApp
        mensaje_texto = (
            f"Hola, me contacto de parte de la empresa *{lead.empresa}* "
            f"(mi nombre es {lead.nombre}) referente a la cotización *{lead.codigo_referencia}*.\n\n"
            f"Tengo un total de *{resumen_lineas}* producto(s) en mi lista de cotización.\n\n"
            f"Quisiera coordinar el presupuesto formal y los detalles de entrega."
        )
        encoded_message = urllib.parse.quote(mensaje_texto)
        whatsapp_url = f"https://wa.me/{self.whatsapp_phone}?text={encoded_message}"

        # 5. Formatear URL de descarga de PDF (sin persistencia local, pasamos los datos del Lead seguros)
        query_params = urllib.parse.urlencode({
            "ref": lead.codigo_referencia,
            "name": lead.nombre,
            "company": lead.empresa,
            "email": str(lead.email),
            "phone": lead.telefono
        })
        pdf_url = f"/presupuesto/descargar/?{query_params}"

        return ConfirmacionPresupuestoResponse(
            lead_id=lead.id,
            codigo_referencia=lead.codigo_referencia,
            whatsapp_url=whatsapp_url,
            pdf_url=pdf_url
        )
