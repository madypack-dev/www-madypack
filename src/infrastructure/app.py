from datetime import date
from pathlib import Path
from typing import Any, cast

import yaml
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Madypack")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/robots.txt", response_class=FileResponse)
async def robots_txt():
    return FileResponse(Path(__file__).resolve().parents[2] / "static" / "robots.txt")


@app.get("/sitemap.xml")
async def sitemap_xml():
    today = date.today().isoformat()
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.madypack.com.ar/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/quienes-somos/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/cotizacion/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/contacto/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/terminos-y-condiciones/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/politica-de-privacidad/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
"""
    return Response(content=xml_content, media_type="application/xml")

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
        context={"site": load_site(), "success": request.query_params.get("success")},
    )


@app.post("/")
async def post_root(request: Request):
    form_data = await request.form()
    if "phone" in form_data:
        return RedirectResponse(url="/?success=quote", status_code=303)
    return RedirectResponse(url="/?success=newsletter", status_code=303)


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
        context={"site": load_site(), "success": request.query_params.get("success")},
    )


@app.post("/cotizacion/")
async def post_cotizacion(request: Request):
    return RedirectResponse(url="/cotizacion/?success=quote", status_code=303)


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


@app.get("/cart/", response_class=HTMLResponse)
async def read_cart(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/cart.html",
        context={"site": load_site()},
    )

