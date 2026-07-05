"""Path: src/infraestructura/rutas/presupuesto.py"""

from functools import partial
from io import BytesIO

from fastapi import APIRouter, Depends, Form, Request
from starlette.datastructures import UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, ValidationError

from src.comercio.adaptadores.repositorios.cookie import RepositorioCarritoCookie
from src.comercio.dominio.modelos.carrito import Carrito
from src.infraestructura.adaptadores.generador_pdf_reportlab import (
    GeneradorPresupuestoPDFReportLab,
)
from src.infraestructura.datos.cargadores import (
    cargar_productos_tienda,
    cargar_site,
    cargar_tarifas,
)
from src.comercio.dominio.modelos.catalogo import ArticuloCatalogo
from src.infraestructura.datos.modelos import SiteConfig
from src.infraestructura.estaticos import resolver_archivo_estatico
from src.infraestructura.logging.logger import get_logger
from src.infraestructura.rutas.base import LoggingRoute, load_site, templates
from src.infraestructura.tenant.resolutor import resolutor_tenant
from src.precios.adaptadores.servicios.cotizador import CotizadorServicio
from src.presupuesto.aplicacion.casos_uso.generar_presupuesto_pdf import (
    CasoUsoGenerarPresupuestoPDF,
)
from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import DatosSolicitante

import httpx
from src.lead.adaptadores.repositorios.chatwoot_contact import ChatwootContactRepository
from src.lead.adaptadores.eventos.noop_publicador import NoOpPublicador
from src.lead.aplicacion.casos_uso.crear_lead import CrearLeadDesdePresupuesto
from src.infraestructura.config.settings import (
    CHATWOOT_URL,
    CHATWOOT_ACCOUNT_ID,
    CHATWOOT_INBOX_ID,
    CHATWOOT_API_TOKEN,
)

def get_http_client(request: Request) -> httpx.AsyncClient:
    """Obtiene el cliente HTTP singleton de la aplicación FastAPI.

    Si no se ha inicializado (por ejemplo, en tests de integración que no disparan el lifespan),
    se inicializa de manera perezosa (lazy load) para evitar excepciones.
    """
    if not hasattr(request.app.state, "http_client"):
        request.app.state.http_client = httpx.AsyncClient(timeout=10.0)
    return request.app.state.http_client

def get_chatwoot_repo(http_client: httpx.AsyncClient = Depends(get_http_client)) -> ChatwootContactRepository:
    """Inyecta el cliente HTTP singleton para construir el repositorio de Chatwoot Contact."""
    return ChatwootContactRepository(
        http_client=http_client,
        base_url=CHATWOOT_URL,
        account_id=CHATWOOT_ACCOUNT_ID,
        api_token=CHATWOOT_API_TOKEN,
    )

def get_caso_uso_lead(
    repo: ChatwootContactRepository = Depends(get_chatwoot_repo),
    tenant: str = Depends(resolutor_tenant)
) -> CrearLeadDesdePresupuesto:
    """Ensambla el caso de uso de lead inyectando el repositorio y parámetros de tenant."""
    site = cargar_site(tenant)
    whatsapp_vendedor = site.whatsapp.phone
    return CrearLeadDesdePresupuesto(
        repositorio=repo,
        publicador_eventos=NoOpPublicador(),
        chatwoot_inbox_id=CHATWOOT_INBOX_ID,
        whatsapp_phone=whatsapp_vendedor,
        registrar_error=logger.error,
    )

router = APIRouter(route_class=LoggingRoute)
logger = get_logger()


class SolicitudPresupuestoForm(BaseModel):
    """Validación de los campos del formulario de cotización."""

    name: str | None = None
    email: EmailStr
    phone: str
    company: str | None = None
    message: str | None = None


def _str_field(value: UploadFile | str | None) -> str | None:
    """Extrae un string limpio de un campo de formulario, descartando UploadFile."""
    if value is None:
        return None
    if isinstance(value, UploadFile):
        return None
    stripped = str(value).strip()
    return stripped if stripped else None


def _str_field_required(value: UploadFile | str | None) -> str:
    """Extrae un string obligatorio de un campo de formulario."""
    result = _str_field(value)
    if result is None:
        return ""
    return result


def _obtener_productos_tienda(tenant: str) -> list[ArticuloCatalogo]:
    """Devuelve el catálogo validado del tenant o una lista vacía si hay error."""
    try:
        return cargar_productos_tienda(tenant).articulos
    except Exception as err:
        logger.error(
            f"Error obteniendo catálogo para tenant '{tenant}': {err}", exc_info=True
        )
        return []


def _obtener_tarifas(tenant: str) -> dict:
    """Devuelve las tarifas validadas del tenant o un diccionario vacío si hay error."""
    try:
        return cargar_tarifas(tenant).model_dump()
    except Exception as err:
        logger.error(
            f"Error obteniendo tarifas para tenant '{tenant}': {err}", exc_info=True
        )
        return {}


def _formatear_moneda(valor: float) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatear_total_bolsas(carrito: Carrito) -> str:
    return f"{carrito.total_bolsas:,} unidades".replace(",", ".")


@router.get("/cotizacion/", response_class=HTMLResponse)
async def read_cotizacion(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
    site: SiteConfig = Depends(load_site),
):
    """Muestra el formulario de cotización junto con el resumen del carrito."""
    productos = _obtener_productos_tienda(tenant)
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_productos_tienda=lambda: productos,
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=partial(_obtener_tarifas, tenant),
        registrar_error=logger.error,
    )

    precio_total = 0.0
    for articulo in carrito.articulos:
        try:
            precio_total += cotizador.calcular_precio_estimado(articulo)
        except Exception as err:
            logger.warning(f"No se pudo cotizar artículo {articulo.id}: {err}")

    precio_estimado_formateado = (
        _formatear_moneda(precio_total) if precio_total > 0 else "A cotizar"
    )
    total_bolsas_formateado = _formatear_total_bolsas(carrito)

    return templates.TemplateResponse(
        request=request,
        name="pages/cotizacion.html",
        context={
            "site": site,
            "cart_items": carrito.articulos,
            "total_bags_formatted": total_bolsas_formateado,
            "estimated_cost_formatted": precio_estimado_formateado,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
            "form_action": "/presupuesto/",
        },
    )


@router.post("/presupuesto/")
async def generar_presupuesto(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
    caso_uso_lead: CrearLeadDesdePresupuesto = Depends(get_caso_uso_lead),
):
    """Procesa los datos de contacto del lead, los envía a Chatwoot y retorna la vista de confirmación."""
    from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest

    site = cargar_site(tenant)
    form_data = await request.form()

    try:
        datos_form = CrearLeadRequest(
            nombre=_str_field_required(form_data.get("name")),
            empresa=_str_field_required(form_data.get("company")),
            telefono=_str_field_required(form_data.get("phone")),
            email=_str_field_required(form_data.get("email")),
        )
    except (ValidationError, ValueError) as err:
        logger.warning(f"Datos de contacto inválidos: {err}")
        return RedirectResponse(url="/cotizacion/?error=datos_invalidos", status_code=303)

    productos = _obtener_productos_tienda(tenant)
    repositorio_carrito = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_productos_tienda=lambda: productos,
        registrar_error=logger.error,
    )
    carrito = repositorio_carrito.obtener_carrito()
    if not carrito.articulos:
        return RedirectResponse(url="/cotizacion/?error=carrito_vacio", status_code=303)

    whatsapp_vendedor = site.whatsapp.phone

    try:
        response_lead = await caso_uso_lead.ejecutar(datos_form, carrito)
    except Exception as err:
        logger.error(f"Falla crítica inesperada en el caso de uso de lead: {err}", exc_info=True)
        import uuid
        import urllib.parse
        from src.lead.aplicacion.dtos.lead_dtos import ConfirmacionPresupuestoResponse

        ref_code = f"COT-ERR-{str(uuid.uuid4())[:8].upper()}"

        # Intentar registrar localmente el lead de contingencia
        try:
            import json
            import os
            from datetime import datetime
            fallback_data = {
                "timestamp": datetime.now().isoformat(),
                "lead_id": f"INFRA-ERR-{uuid.uuid4()}",
                "codigo_referencia": ref_code,
                "nombre": datos_form.nombre,
                "empresa": datos_form.empresa,
                "email": str(datos_form.email),
                "telefono": datos_form.telefono,
                "error": f"Falla crítica de infraestructura: {str(err)}"
            }
            os.makedirs("logs", exist_ok=True)
            with open("logs/failed_leads.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(fallback_data) + "\n")
        except Exception as file_err:
            logger.error(f"No se pudo guardar el lead de emergencia en logs/failed_leads.log: {file_err}")

        # Construir respuesta mockeada segura para evitar 500 y permitir la continuidad comercial
        encoded_message = urllib.parse.quote(
            f"Hola, mi nombre es {datos_form.nombre} de la empresa *{datos_form.empresa}*. "
            f"Ocurrió un inconveniente al generar la cotización online ({ref_code}). "
            f"Quisiera coordinar la cotización comercial directamente por acá."
        )
        whatsapp_url = f"https://wa.me/{whatsapp_vendedor}?text={encoded_message}"
        query_params = urllib.parse.urlencode({
            "ref": ref_code,
            "name": datos_form.nombre,
            "company": datos_form.empresa,
            "email": str(datos_form.email),
            "phone": datos_form.telefono
        })
        pdf_url = f"/presupuesto/descargar/?{query_params}"

        response_lead = ConfirmacionPresupuestoResponse(
            lead_id=f"ERR-{uuid.uuid4()}",
            codigo_referencia=ref_code,
            whatsapp_url=whatsapp_url,
            pdf_url=pdf_url
        )

    return templates.TemplateResponse(
        request=request,
        name="pages/confirmacion_presupuesto.html",
        context={"site": site, "response": response_lead},
    )


@router.get("/presupuesto/descargar/")
async def descargar_presupuesto(
    request: Request,
    ref: str,
    name: str,
    company: str,
    email: EmailStr,
    phone: str,
    tenant: str = Depends(resolutor_tenant),
):
    """Genera al vuelo el PDF de presupuesto a partir de los datos recibidos (sin persistencia local)."""
    site = cargar_site(tenant)
    
    datos_solicitante = DatosSolicitante(
        nombre=name,
        email=str(email),
        telefono=phone,
        empresa=company,
        mensaje=f"Presupuesto de referencia {ref}",
    )

    logo_src = site.header.logo.src
    logo_path_obj = (
        resolver_archivo_estatico(tenant, f"images/{logo_src}") if logo_src else None
    )
    logo_path = str(logo_path_obj) if logo_path_obj else None

    identidad_visual = IdentidadVisual(
        brand=site.site.brand,
        tagline=site.site.tagline,
        logo_path=logo_path,
        email=site.home.contact.email,
        telefono=site.home.contact.whatsapp_label,
        direccion=site.home.contact.address,
        whatsapp=site.whatsapp.phone,
        url=site.schema_config.url,
    )

    productos = _obtener_productos_tienda(tenant)
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_productos_tienda=lambda: productos,
        registrar_error=logger.error,
    )

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=partial(_obtener_tarifas, tenant),
        registrar_error=logger.error,
    )

    generador_pdf = GeneradorPresupuestoPDFReportLab()
    caso_uso = CasoUsoGenerarPresupuestoPDF(
        repositorio_carrito=repositorio,
        servicio_precios=cotizador,
        generador_pdf=generador_pdf,
        registrar_error=logger.error,
    )

    try:
        pdf_bytes = caso_uso.ejecutar(
            datos_solicitante=datos_solicitante,
            identidad_visual=identidad_visual,
            validez_dias=site.presupuesto.validez_dias,
            condiciones_comerciales=site.presupuesto.condiciones_comerciales,
        )
    except ValueError as err:
        logger.warning(f"No se pudo generar presupuesto: {err}")
        return RedirectResponse(url=f"/cotizacion/?error={err}", status_code=303)
    except Exception as err:
        logger.error(f"Error generando PDF de presupuesto: {err}", exc_info=True)
        return RedirectResponse(url="/cotizacion/?error=pdf_error", status_code=303)

    filename = f"presupuesto-{ref}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
