from contextlib import asynccontextmanager
from datetime import date
import mimetypes

from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import FileResponse

from src.infraestructura.config.settings import APP_TITLE, MAPEO_TENANTS, MAPEO_PUERTOS
from src.infraestructura.estaticos import resolver_archivo_estatico
from src.infraestructura.datos.cargadores import (
    cargar_site,
    cargar_productos_tienda,
    cargar_tarifas,
)
from src.infraestructura.logging.logger import configurar_logging, get_logger
from src.infraestructura.rutas.paginas import router as paginas_router
from src.infraestructura.rutas.carrito import router as carrito_router
from src.infraestructura.rutas.presupuesto import router as presupuesto_router
from src.infraestructura.tenant.resolutor import resolutor_tenant

configurar_logging()
logger = get_logger()


def _tenants_conocidos() -> set[str]:
    return set(MAPEO_TENANTS.values()) | set(MAPEO_PUERTOS.values())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida los YAML de todos los tenants conocidos antes de arrancar."""
    for tenant in sorted(_tenants_conocidos()):
        logger.info(f"Validando YAML del tenant '{tenant}'...")
        cargar_site(tenant)
        cargar_productos_tienda(tenant)
        cargar_tarifas(tenant)
        logger.info(f"Tenant '{tenant}' validado correctamente.")
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan)


@app.get("/static/{path:path}", name="static")
async def static_files(path: str, tenant: str = Depends(resolutor_tenant)):
    """Sirve archivos estáticos resolviendo primero la carpeta del tenant."""
    file_path = resolver_archivo_estatico(tenant, path)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Not found")

    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path, media_type=content_type)


@app.get("/robots.txt")
async def robots_txt(request: Request, tenant: str = Depends(resolutor_tenant)):
    """Sirve robots.txt del tenant si existe; si no, genera uno dinámico.

    La versión dinámica apunta al sitemap del host actual, evitando
    hardcodear dominios de un tenant particular.
    """
    file_path = resolver_archivo_estatico(tenant, "robots.txt", incluir_fallback=False)
    if file_path is not None:
        return FileResponse(file_path)

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", "localhost")
    base_url = f"{scheme}://{host}".rstrip("/")

    content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, tenant: str = Depends(resolutor_tenant)):
    """Genera el sitemap usando el dominio del tenant actual."""
    today = date.today().isoformat()

    # Respetar el esquema de un posible reverse proxy (X-Forwarded-Proto).
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", "localhost")
    base_url = f"{scheme}://{host}".rstrip("/")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
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


app.include_router(paginas_router)
app.include_router(carrito_router)
app.include_router(presupuesto_router)
