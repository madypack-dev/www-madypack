"""Rutas de infraestructura FastAPI para la personalización de bolsas y generación de fotopolímeros."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from src.application.personalizacion.generate_customization import (
    CasoUsoGenerarPersonalizacion,
    SolicitudPersonalizacionDTO,
)
from src.infrastructure.fastapi.dependencies import get_caso_uso_personalizacion
from src.infrastructure.fastapi.routes.base import load_site, logger, templates
from src.infrastructure.pyyaml.models import SiteConfig

router = APIRouter(tags=["Customization"])


@router.get("/personalizar/", response_class=HTMLResponse)
async def ver_personalizador(request: Request, site: SiteConfig = Depends(load_site)):
    """Muestra la interfaz interactiva para personalizar bolsas."""
    return templates.TemplateResponse(
        request=request,
        name="pages/personalizar.html",
        context={"site": site, "resultado": None},
    )


@router.post("/personalizar/procesar", response_class=HTMLResponse)
async def procesar_personalizacion(
    request: Request,
    ancho_cm: float = Form(20.0),
    alto_cm: float = Form(30.0),
    fuelle_cm: float = Form(10.0),
    color_papel: str = Form("#D2B48C"),
    color_tinta: str = Form("#000000"),
    tipo_manija: str = Form("manija_retorcida"),
    diseno: UploadFile = File(...),
    site: SiteConfig = Depends(load_site),
    caso_uso: CasoUsoGenerarPersonalizacion = Depends(get_caso_uso_personalizacion),
):
    """Procesa el diseño subido y genera el SVG de fotopolímero y el mockup 2D."""
    contenido_bytes = await diseno.read()
    if not contenido_bytes:
        logger.warning("Intento de personalización con archivo vacío.")
        return templates.TemplateResponse(
            request=request,
            name="pages/personalizar.html",
            context={
                "site": site,
                "error": "Debes seleccionar un archivo de imagen o logo válido.",
            },
        )

    solicitud = SolicitudPersonalizacionDTO(
        ancho_cm=ancho_cm,
        alto_cm=alto_cm,
        fuelle_cm=fuelle_cm,
        color_papel=color_papel,
        color_tinta=color_tinta,
        tipo_manija=tipo_manija,
        contenido_bytes=contenido_bytes,
        mime_type=diseno.content_type or "image/png",
    )

    try:
        resultado = caso_uso.ejecutar(solicitud)
    except Exception as err:
        logger.error(f"Error procesando personalización: {err}")
        return templates.TemplateResponse(
            request=request,
            name="pages/personalizar.html",
            context={"site": site, "error": f"Error al procesar el diseño: {err}"},
        )

    return templates.TemplateResponse(
        request=request,
        name="pages/personalizar.html",
        context={
            "site": site,
            "resultado": resultado,
            "ancho_cm": ancho_cm,
            "alto_cm": alto_cm,
            "fuelle_cm": fuelle_cm,
            "color_papel": color_papel,
            "color_tinta": color_tinta,
            "tipo_manija": tipo_manija,
        },
    )
