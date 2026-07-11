"""Path: src/infraestructura/rutas/presupuesto.py"""

import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, Request
from starlette.datastructures import UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import EmailStr, ValidationError

from src.adapters.comercio.repositorios.cookie import RepositorioCarritoCookie
from src.domain.comercio.modelos.carrito import Carrito
from src.application.comercio.casos_uso.carrito import CasoUsoObtenerResumenCarrito
from src.adapters.presupuesto.generadores.pdf_reportlab import (
    GeneradorPresupuestoPDFReportLab,
)
from src.infrastructure.datos.modelos import SiteConfig
from src.infrastructure.datos.proveedores import (
    obtener_productos_tienda,
    obtener_tarifas,
)
from src.infrastructure.estaticos import resolver_archivo_estatico
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.rutas.base import load_site, templates
from src.application.lead.dtos.lead_dtos import CrearLeadRequest
from src.domain.lead.modelos.lead import Lead
from src.adapters.precios.servicios.cotizador import CotizadorServicio
from src.adapters.presupuesto.presentadores.confirmacion import (
    PresentadorConfirmacionPresupuesto,
)
from src.adapters.presupuesto.repositorios.fallback_archivo import (
    RegistroFallbackArchivo,
)
from src.application.presupuesto.casos_uso.generar_presupuesto_pdf import (
    CasoUsoGenerarPresupuestoPDF,
)
from src.application.presupuesto.casos_uso.procesar_solicitud_presupuesto import (
    ProcesarSolicitudPresupuesto,
)
from src.application.presupuesto.helpers import construir_lineas_presupuesto
from src.domain.presupuesto.modelos.identidad_visual import IdentidadVisual
from src.domain.presupuesto.modelos.presupuesto import DatosSolicitante

from src.infrastructure.config.settings import CHATWOOT_INBOX_ID
from src.infrastructure.dependencias import get_chatwoot_repo

logger = get_logger()


def get_caso_uso_presupuesto(
    repo=Depends(get_chatwoot_repo),
) -> ProcesarSolicitudPresupuesto:
    """Ensambla el caso de uso de presupuesto inyectando el repositorio."""
    return ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=CHATWOOT_INBOX_ID,
        registro_fallback=RegistroFallbackArchivo(),
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
):
    """Muestra el formulario de cotización junto con el resumen del carrito."""
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=obtener_tarifas,
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoObtenerResumenCarrito(registrar_error=logger.warning)
    resumen = caso_uso.ejecutar(carrito, cotizador)

    return templates.TemplateResponse(
        request=request,
        name="pages/cotizacion.html",
        context={
            "site": site,
            "cart_items": resumen.articulos,
            "total_bags_formatted": resumen.total_bolsas_formateado,
            "estimated_cost_formatted": resumen.precio_estimado_formateado,
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
        lead = await caso_uso.ejecutar(datos_form, carrito)
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
    name: str,
    company: str,
    email: EmailStr,
    phone: str,
    site: SiteConfig = Depends(load_site),
):
    """Genera al vuelo el PDF de presupuesto a partir de los datos recibidos (sin persistencia local)."""
    datos_solicitante = DatosSolicitante(
        nombre=name,
        email=str(email),
        telefono=phone,
        empresa=company,
        mensaje=f"Presupuesto de referencia {ref}",
    )

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

    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=obtener_tarifas,
        registrar_error=logger.error,
    )

    lineas = construir_lineas_presupuesto(carrito, cotizador, logger.error)

    generador_pdf = GeneradorPresupuestoPDFReportLab()
    caso_uso = CasoUsoGenerarPresupuestoPDF(
        generador_pdf=generador_pdf,
        registrar_error=logger.error,
    )

    try:
        pdf_bytes = caso_uso.ejecutar(
            datos_solicitante=datos_solicitante,
            lineas=lineas,
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
