from typing import Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infraestructura.rutas.base import templates, load_site, LoggingRoute

router = APIRouter(route_class=LoggingRoute)


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


@router.get("/cotizacion/", response_class=HTMLResponse)
async def read_cotizacion(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/cotizacion.html",
        context={"site": site, "success": request.query_params.get("success")},
    )


@router.post("/cotizacion/")
async def post_cotizacion(request: Request):
    return RedirectResponse(url="/cotizacion/?success=quote", status_code=303)


@router.get("/contacto/", response_class=HTMLResponse)
async def read_contacto(request: Request, site: dict[str, Any] = Depends(load_site)):
    return templates.TemplateResponse(
        request=request,
        name="pages/contacto.html",
        context={"site": site},
    )


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
