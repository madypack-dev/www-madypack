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
            precio_total += cotizador.calcular_precio_estimado(
                articulo.id, articulo.cantidad
            )
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
):
    """Procesa los datos de contacto del lead, los envía a Chatwoot y retorna la vista de confirmación."""
    from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest
    from src.lead.adaptadores.repositorios.chatwoot_contact import ChatwootContactRepository
    from src.lead.adaptadores.eventos.noop_publicador import NoOpPublicador
    from src.lead.aplicacion.casos_uso.crear_lead import CrearLeadDesdePresupuesto
    from src.infraestructura.config.settings import (
        CHATWOOT_URL,
        CHATWOOT_ACCOUNT_ID,
        CHATWOOT_INBOX_ID,
        CHATWOOT_API_TOKEN,
    )
    import httpx

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

    async with httpx.AsyncClient() as http_client:
        chatwoot_repo = ChatwootContactRepository(
            http_client=http_client,
            base_url=CHATWOOT_URL,
            account_id=CHATWOOT_ACCOUNT_ID,
            api_token=CHATWOOT_API_TOKEN,
        )
        publicador = NoOpPublicador()
        
        whatsapp_vendedor = site.whatsapp.phone

        caso_uso_lead = CrearLeadDesdePresupuesto(
            repositorio=chatwoot_repo,
            publicador_eventos=publicador,
            chatwoot_inbox_id=CHATWOOT_INBOX_ID,
            whatsapp_phone=whatsapp_vendedor,
            registrar_error=logger.error,
        )

        response_lead = await caso_uso_lead.ejecutar(datos_form, carrito)

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
