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
from src.infraestructura.datos.modelos import ArticuloCatalogo, SiteConfig
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
    """Genera y devuelve el PDF de presupuesto a partir del carrito y datos del solicitante."""
    site = cargar_site(tenant)
    form_data = await request.form()

    try:
        datos_form = SolicitudPresupuestoForm(
            name=_str_field(form_data.get("name")),
            email=_str_field_required(form_data.get("email")),
            phone=_str_field_required(form_data.get("phone")),
            company=_str_field(form_data.get("company")),
            message=_str_field(form_data.get("message")),
        )
    except ValidationError as err:
        logger.warning(f"Datos de solicitud inválidos: {err}")
        return RedirectResponse(url="/cotizacion/?error=datos_invalidos", status_code=303)

    datos_solicitante = DatosSolicitante(
        nombre=datos_form.name,
        email=str(datos_form.email),
        telefono=datos_form.phone,
        empresa=datos_form.company,
        mensaje=datos_form.message,
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

    brand_slug = site.site.brand.lower().replace(" ", "-")
    filename = f"presupuesto-{brand_slug}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
