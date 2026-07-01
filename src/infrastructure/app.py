from pathlib import Path
from typing import Any, cast

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Madypack")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/robots.txt", response_class=FileResponse)
async def robots_txt():
    return FileResponse(Path(__file__).resolve().parents[2] / "static" / "robots.txt")


@app.get("/sitemap.xml", response_class=FileResponse)
async def sitemap_xml():
    return FileResponse(Path(__file__).resolve().parents[2] / "static" / "sitemap.xml")

templates = Jinja2Templates(directory="templates")

SITE_YAML = Path(__file__).resolve().parents[2] / "data" / "site.yml"


def load_site() -> dict[str, Any]:
    if not SITE_YAML.exists():
        return {}
    return cast(dict[str, Any], yaml.safe_load(SITE_YAML.read_text(encoding="utf-8")) or {})


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"site": load_site()},
    )


@app.get("/quienes-somos/", response_class=HTMLResponse)
async def read_quienes_somos(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/quienes-somos.html",
        context={"site": load_site()},
    )


@app.get("/cotizacion/", response_class=HTMLResponse)
async def read_cotizacion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/cotizacion.html",
        context={"site": load_site()},
    )


@app.get("/contacto/", response_class=HTMLResponse)
async def read_contacto(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/contacto.html",
        context={"site": load_site()},
    )


@app.get("/terminos-y-condiciones/", response_class=HTMLResponse)
async def read_terminos_y_condiciones(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/terminos-y-condiciones.html",
        context={"site": load_site()},
    )


@app.get("/politica-de-privacidad/", response_class=HTMLResponse)
async def read_politica_de_privacidad(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/politica-de-privacidad.html",
        context={"site": load_site()},
    )

