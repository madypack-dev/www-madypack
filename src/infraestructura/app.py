from contextlib import asynccontextmanager
from datetime import date
import mimetypes

from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

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


def compilar_bundle_css():
    """Une todos los archivos CSS de la aplicación en un único static/css/bundle.css

    para optimizar la entrega reduciendo las peticiones HTTP concurrentes (evitando render-blocking).
    """
    try:
        from pathlib import Path
        infra_dir = Path(__file__).resolve().parent
        root_dir = infra_dir.parents[1]
        css_dir = root_dir / "static" / "css"

        css_files = [
            css_dir / "base" / "variables.css",
            css_dir / "base" / "reset.css",
            css_dir / "layout.css",
            css_dir / "components" / "buttons.css",
            css_dir / "components" / "social.css",
            css_dir / "components" / "header.css",
            css_dir / "components" / "footer.css",
            css_dir / "components" / "home.css",
            css_dir / "components" / "cart.css",
            css_dir / "components" / "tienda.css",
            css_dir / "components" / "cookie-banner.css",
            css_dir / "components" / "confirmation.css",
        ]

        bundle_content = []
        for file_path in css_files:
            if file_path.exists():
                rel_path = file_path.relative_to(root_dir / "static")
                bundle_content.append(f"/* --- Start of {rel_path} --- */")
                bundle_content.append(file_path.read_text(encoding="utf-8"))
                bundle_content.append(f"/* --- End of {rel_path} --- */\n")
            else:
                logger.warning(f"Archivo CSS no encontrado para empaquetar: {file_path}")

        bundle_file = css_dir / "bundle.css"
        bundle_file.write_text("\n".join(bundle_content), encoding="utf-8")
        logger.info(f"CSS bundle compilado con éxito en {bundle_file}")
    except Exception as exc:
        logger.error(f"Error al compilar el bundle de CSS: {exc}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida los YAML de todos los tenants conocidos y compila el CSS bundle antes de arrancar."""
    compilar_bundle_css()
    for tenant in sorted(_tenants_conocidos()):
        logger.info(f"Validando YAML del tenant '{tenant}'...")
        cargar_site(tenant)
        cargar_productos_tienda(tenant)
        cargar_tarifas(tenant)
        logger.info(f"Tenant '{tenant}' validado correctamente.")
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan, redirect_slashes=False)


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Middleware global para normalizar URLs redirigiendo permanentemente (301) a trailing slash.

    Evita redirigir archivos estáticos, rutas del sistema (/health, /robots.txt, etc.) y URLs con extensión.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Excluir rutas específicas que no deben ser normalizadas con /
        exclusiones = {"/health", "/robots.txt", "/sitemap.xml"}
        es_estatico = path.startswith("/static/")
        tiene_extension = "." in path.split("/")[-1]

        if (
            path != "/"
            and not path.endswith("/")
            and not es_estatico
            and not tiene_extension
            and path not in exclusiones
        ):
            query = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(url=f"{path}/{query}", status_code=301)

        return await call_next(request)


app.add_middleware(TrailingSlashMiddleware)


@app.middleware("http")
async def agregar_request_id_middleware(request: Request, call_next):
    import uuid
    import structlog
    # Limpiar y asociar request ID único en las variables de contexto
    structlog.contextvars.clear_contextvars()
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Excepción no manejada en el request", error=str(exc))
    from fastapi.responses import HTMLResponse
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Error en el Servidor | Madypack</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; color: #333; }
            h1 { color: #2853A1; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>Ha ocurrido un error inesperado</h1>
        <p>Nuestro equipo técnico ha sido notificado. Por favor, intente nuevamente más tarde.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=500)


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools_silent():
    """Silencia el request automático de Chrome DevTools retornando 200 vacío."""
    return {}


@app.get("/health", include_in_schema=False)
async def health_check():
    """Endpoint liviano para validar que el ecommerce y sus integraciones básicas responden."""
    from fastapi.responses import JSONResponse
    import httpx
    from src.infraestructura.config.settings import CHATWOOT_URL
    
    health_status = {
        "status": "healthy",
        "timestamp": date.today().isoformat(),
        "services": {
            "catalog": "ok",
            "chatwoot": "unknown"
        }
    }
    
    try:
        cargar_productos_tienda("default")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["catalog"] = f"error: {str(e)}"
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.head(CHATWOOT_URL, timeout=1.0)
            health_status["services"]["chatwoot"] = "ok" if resp.status_code < 500 else f"status_{resp.status_code}"
    except Exception as e:
        health_status["services"]["chatwoot"] = f"error: {str(e)}"
        
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


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
Disallow: /carrito/
Disallow: /presupuesto/
Disallow: /presupuesto/descargar/

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

    # Cargar los productos del tenant para indexarlos de forma individual
    try:
        productos = cargar_productos_tienda(tenant).articulos
    except Exception:
        productos = []

    product_urls = ""
    for producto in productos:
        product_urls += f"""  <url>
    <loc>{base_url}/tienda/{producto.url_slug}/</loc>
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
    <loc>{base_url}/tienda/</loc>
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


app.include_router(paginas_router)
app.include_router(carrito_router)
app.include_router(presupuesto_router)
