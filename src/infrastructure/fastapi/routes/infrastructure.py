"""Rutas utilitarias de infraestructura: health, robots, sitemap, devtools."""

from datetime import date

from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse, JSONResponse, Response, RedirectResponse

from src.infrastructure.config.settings import CHATWOOT_URL
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.infrastructure.fastapi.dependencies import get_http_client_adapter, get_repositorio_catalogo
from src.infrastructure.estaticos import resolver_archivo_estatico
from src.infrastructure.structlog.logger import get_logger
from src.domain.lead.http_client import IHttpClient

logger = get_logger()
router = APIRouter()


@router.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools_silent():
    """Silencia el request automático de Chrome DevTools retornando 200 vacío."""
    return {}


@router.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    """Redirecciona la petición automática del favicon al recurso estático."""
    return RedirectResponse(url="/static/images/favicon.ico")


@router.get("/health", include_in_schema=False)
async def health_check(
    request: Request,
    http_client: IHttpClient = Depends(get_http_client_adapter),
    repositorio_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
):
    """Endpoint liviano para validar que el ecommerce responde."""

    health_status = {
        "status": "healthy",
        "timestamp": date.today().isoformat(),
        "services": {
            "catalog": "ok",
            "chatwoot": "unknown",
        },
    }

    try:
        repositorio_catalogo.obtener_todos()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["catalog"] = f"error: {str(e)}"

    try:
        resp = await http_client.head(CHATWOOT_URL, timeout=1.0)
        health_status["services"]["chatwoot"] = (
            "ok" if resp.status_code < 500 else f"status_{resp.status_code}"
        )
    except Exception as e:
        health_status["services"]["chatwoot"] = f"error: {str(e)}"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/robots.txt")
async def robots_txt(request: Request):
    """Sirve robots.txt si existe; si no, genera uno dinámico."""
    file_path = resolver_archivo_estatico("robots.txt")
    if file_path is not None:
        return FileResponse(file_path)

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", "localhost")
    base_url = f"{scheme}://{host}".rstrip("/")

    content = f"""User-agent: *
Allow: /
Disallow: /cart/
Disallow: /presupuesto/
Disallow: /presupuesto/descargar/

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@router.get("/sitemap.xml")
async def sitemap_xml(
    request: Request,
    repositorio_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
):
    """Genera el sitemap."""
    today = date.today().isoformat()

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", "localhost")
    base_url = f"{scheme}://{host}".rstrip("/")

    try:
        productos = repositorio_catalogo.obtener_todos()
    except Exception:
        productos = []

    product_urls = ""
    for producto in productos:
        if not getattr(producto, "visible", False):
            continue
        product_urls += f"""  <url>
    <loc>{base_url}/productos/{producto.url_slug}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
"""

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/productos/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
{product_urls}  <url>
    <loc>{base_url}/quienes-somos/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/cotizacion/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/contacto/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/terminos-y-condiciones/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{base_url}/politica-de-privacidad/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
"""
    return Response(content=xml_content, media_type="application/xml")
