"""Path: src/infraestructura/rutas/presupuesto.py"""

import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, Request
from starlette.datastructures import UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import EmailStr, ValidationError

from src.adapters.gateways.commerce_cookie_repository import RepositorioCarritoCookie
from src.application.commerce.cart_use_cases import CasoUsoObtenerResumenCarrito
from src.infrastructure.pyyaml.models import SiteConfig

from src.infrastructure.estaticos import resolver_archivo_estatico
from src.infrastructure.structlog.logger import get_logger
from src.infrastructure.fastapi.routes.base import load_site, templates
from src.application.lead.lead_dtos import CrearLeadRequest
from src.adapters.presenters.commerce_presentation_helper import formatear_precio, formatear_unidades

from src.domain.lead.lead import Lead
from src.adapters.gateways.pricing_service import CotizadorServicio
from src.adapters.presenters.quote_confirmation_presenter import PresentadorConfirmacionPresupuesto
from src.application.quote.generate_quote_pdf import CasoUsoGenerarPresupuestoPDF

from src.application.quote.process_quote_request import ProcesarSolicitudPresupuesto

from src.application.quote.quote_helpers import construir_lineas_presupuesto
from src.domain.quote.visual_identity import IdentidadVisual
from src.domain.quote.quote import DatosSolicitante
from src.domain.quote.quote_repository import IQuoteRepository

from src.infrastructure.config.settings import CHATWOOT_INBOX_ID
from src.infrastructure.fastapi.dependencies import (
    get_chatwoot_repo,
    get_cotizador,
    get_registro_fallback,
    get_caso_uso_generar_pdf,
    get_quote_repo,
)

logger = get_logger()


def get_caso_uso_presupuesto(
    repo=Depends(get_chatwoot_repo),
    registro_fallback=Depends(get_registro_fallback),
    quote_repo: IQuoteRepository = Depends(get_quote_repo),
    cotizador: CotizadorServicio = Depends(get_cotizador),
) -> ProcesarSolicitudPresupuesto:
    """Ensambla el caso de uso de presupuesto inyectando el repositorio."""
    return ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=CHATWOOT_INBOX_ID,
        registro_fallback=registro_fallback,
        quote_repository=quote_repo,
        cotizador=cotizador,
        registrar_error=logger.error,
    )


router = APIRouter()


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


@router.get("/cotizacion/", response_class=HTMLResponse)
async def read_cotizacion(
    request: Request,
    site: SiteConfig = Depends(load_site),
    cotizador: CotizadorServicio = Depends(get_cotizador),
):
    """Muestra el formulario de cotización junto con el resumen del carrito."""
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    caso_uso = CasoUsoObtenerResumenCarrito(registrar_error=logger.warning)
    resumen = caso_uso.ejecutar(carrito, cotizador)

    return templates.TemplateResponse(
        request=request,
        name="pages/cotizacion.html",
        context={
            "site": site,
            "cart_items": resumen.articulos,
            "total_bags_formatted": formatear_unidades(resumen.total_bolsas),
            "estimated_cost_formatted": formatear_precio(resumen.precio_total),
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
            "form_action": "/presupuesto/",
        },
    )


@router.post("/presupuesto/")
async def generar_presupuesto(
    request: Request,
    caso_uso: ProcesarSolicitudPresupuesto = Depends(get_caso_uso_presupuesto),
    site: SiteConfig = Depends(load_site),
):
    """Procesa los datos de contacto y retorna la vista de confirmación."""
    form_data = await request.form()

    # Soporte híbrido para wpforms (cotización general/checkout) y campos estándar (landing/tests)
    nombre = _str_field(form_data.get("wpforms[fields][3]")) or _str_field(form_data.get("name"))
    email = _str_field(form_data.get("wpforms[fields][11]")) or _str_field(form_data.get("email"))
    telefono = _str_field(form_data.get("wpforms[fields][10]")) or _str_field(form_data.get("phone"))
    empresa = _str_field(form_data.get("wpforms[fields][12]")) or _str_field(form_data.get("company"))
    mensaje = _str_field(form_data.get("wpforms[fields][2]")) or _str_field(form_data.get("message"))

    logger.debug(
        "Formulario de cotización recibido",
        form_keys=list(form_data.keys()),
        nombre=nombre,
        email=email,
        telefono=telefono,
        empresa=empresa,
    )

    try:
        datos_form = CrearLeadRequest(
            nombre=_str_field_required(nombre),
            empresa=_str_field_required(empresa) if empresa else "Particular",
            telefono=_str_field_required(telefono),
            email=_str_field_required(email),
        )
    except (ValidationError, ValueError) as err:
        logger.warning(
            "Datos de contacto inválidos",
            error=str(err),
            nombre=nombre,
            email=email,
        )
        return RedirectResponse(url="/cotizacion/?error=datos_invalidos", status_code=303)

    repositorio_carrito = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )
    carrito = repositorio_carrito.obtener_carrito()

    presentador = PresentadorConfirmacionPresupuesto(
        whatsapp_phone=site.whatsapp.phone,
    )

    try:
        lead = await caso_uso.ejecutar(
            datos_form,
            carrito,
            validez_dias=site.presupuesto.validez_dias,
            condiciones_comerciales=site.presupuesto.condiciones_comerciales,
        )
        response = presentador.presentar(lead, carrito, mensaje)
    except Exception as err:
        ref_code = f"COT-ERR-{str(uuid.uuid4())[:8].upper()}"
        logger.exception(
            "Error procesando solicitud de presupuesto",
            error=str(err),
            ref_code=ref_code,
        )
        lead_emergencia = Lead.crear_emergencia(
            nombre=datos_form.nombre,
            empresa=datos_form.empresa,
            telefono=datos_form.telefono,
            email=datos_form.email,
        )
        lead_emergencia.id = f"ERR-{uuid.uuid4()}"
        response = presentador.presentar_emergencia(lead_emergencia, ref_code)

    return templates.TemplateResponse(
        request=request,
        name="pages/confirmacion_presupuesto.html",
        context={"site": site, "response": response},
    )


@router.get("/presupuesto/descargar/")
async def descargar_presupuesto(
    request: Request,
    ref: str,
    site: SiteConfig = Depends(load_site),
    quote_repo: IQuoteRepository = Depends(get_quote_repo),
    caso_uso_pdf: CasoUsoGenerarPresupuestoPDF = Depends(get_caso_uso_generar_pdf),
):
    """Genera al vuelo el PDF de presupuesto a partir de los datos persistidos localmente."""
    presupuesto = quote_repo.obtener_por_referencia(ref)
    if not presupuesto:
        logger.warning(f"Presupuesto {ref} no encontrado para descarga.")
        return RedirectResponse(url=f"/cotizacion/?error=Presupuesto {ref} no encontrado", status_code=303)

    logo_src = site.header.logo.src
    logo_path_obj = (
        resolver_archivo_estatico(f"images/{logo_src}") if logo_src else None
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

    try:
        pdf_bytes = caso_uso_pdf.ejecutar(
            datos_solicitante=presupuesto.datos_solicitante,
            lineas=presupuesto.lineas,
            identidad_visual=identidad_visual,
            validez_dias=presupuesto.validez_dias,
            condiciones_comerciales=presupuesto.condiciones_comerciales,
        )
    except Exception as err:
        logger.error(f"Error generando PDF de presupuesto: {err}", exc_info=True)
        return RedirectResponse(url="/cotizacion/?error=pdf_error", status_code=303)

    filename = f"presupuesto-{ref}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
