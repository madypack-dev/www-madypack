from typing import Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infrastructure.rutas.base import templates, load_site, logger
from src.domain.lead.modelos.lead import Lead
from src.infrastructure.dependencias import get_chatwoot_repo
from src.infrastructure.config.settings import CHATWOOT_INBOX_ID

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"site": site, "success": request.query_params.get("success")},
    )


@router.post("/")
async def post_root(request: Request):
    form_data = await request.form()
    if "phone" in form_data:
        return RedirectResponse(url="/?success=quote", status_code=303)
    return RedirectResponse(url="/?success=newsletter", status_code=303)


@router.get("/quienes-somos/", response_class=HTMLResponse)
async def read_quienes_somos(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/quienes-somos.html",
        context={"site": site},
    )


@router.get("/contacto/", response_class=HTMLResponse)
async def read_contacto(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/contacto.html",
        context={
            "site": site,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error")
        },
    )


@router.post("/contacto/")
async def post_contacto(
    request: Request,
    repo = Depends(get_chatwoot_repo),
):
    form_data = await request.form()
    nombre = form_data.get("wpforms[fields][0]")
    telefono = form_data.get("wpforms[fields][4]")
    email = form_data.get("wpforms[fields][1]")
    mensaje = form_data.get("wpforms[fields][2]")

    if not nombre or not telefono or not email or not mensaje:
        logger.warning("Datos de contacto faltantes en formulario")
        return RedirectResponse(url="/contacto/?error=datos_invalidos", status_code=303)

    try:
        lead = Lead.crear_contacto(
            nombre=str(nombre),
            empresa="Contacto Web",
            telefono=str(telefono),
            email=str(email)  # type: ignore
        )

        try:
            await repo.guardar(lead, CHATWOOT_INBOX_ID)
            logger.info(f"Contacto de {nombre} enviado a Chatwoot con referencia {lead.codigo_referencia}")
        except Exception as err:
            logger.error(f"Error de integración con Chatwoot en contacto: {err}")

    except Exception as err:
        logger.warning(f"Datos de contacto inválidos en formulario: {err}")
        return RedirectResponse(url="/contacto/?error=datos_invalidos", status_code=303)

    return RedirectResponse(url="/contacto/?success=contacto", status_code=303)


@router.get("/terminos-y-condiciones/", response_class=HTMLResponse)
async def read_terminos_y_condiciones(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/terminos-y-condiciones.html",
        context={"site": site},
    )


@router.get("/politica-de-privacidad/", response_class=HTMLResponse)
async def read_politica_de_privacidad(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/politica-de-privacidad.html",
        context={"site": site},
    )
