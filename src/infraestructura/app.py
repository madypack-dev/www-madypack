from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
import mimetypes

from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import FileResponse

from src.infraestructura.config.settings import APP_TITLE, MAPEO_TENANTS, MAPEO_PUERTOS
from src.infraestructura.datos.cargadores import (
    cargar_site,
    cargar_carrito_defecto,
    cargar_tarifas,
)
from src.infraestructura.logging.logger import configurar_logging, get_logger
from src.infraestructura.rutas.paginas import router as paginas_router
from src.infraestructura.rutas.carrito import router as carrito_router
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
        cargar_carrito_defecto(tenant)
        cargar_tarifas(tenant)
        logger.info(f"Tenant '{tenant}' validado correctamente.")
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


def _resolve_static_file(tenant: str, relative_path: str) -> Path | None:
    """Busca un archivo estático primero en el tenant y luego en la base.

    Devuelve None si no se encuentra o si el path intenta salir de STATIC_DIR.
    """
    relative_path = relative_path.lstrip("/")
    if ".." in relative_path:
        return None

    candidates = [
        STATIC_DIR / "tenants" / tenant / relative_path,
        STATIC_DIR / relative_path,
    ]

    static_root = STATIC_DIR.resolve()
    for candidate in candidates:
        try:
            full_path = candidate.resolve()
        except (OSError, RuntimeError):
            continue
        if not str(full_path).startswith(str(static_root)):
            continue
        if full_path.is_file():
            return full_path
    return None


@app.get("/static/{path:path}", name="static")
async def static_files(path: str, tenant: str = Depends(resolutor_tenant)):
    """Sirve archivos estáticos resolviendo primero la carpeta del tenant."""
    file_path = _resolve_static_file(tenant, path)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Not found")

    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path, media_type=content_type)


@app.get("/robots.txt", response_class=FileResponse)
async def robots_txt(tenant: str = Depends(resolutor_tenant)):
    """Sirve robots.txt del tenant si existe; si no, el genérico."""
    file_path = _resolve_static_file(tenant, "robots.txt")
    if file_path is None:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(file_path)


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
