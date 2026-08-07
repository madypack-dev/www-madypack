from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from src.infrastructure.config.settings import APP_TITLE
from src.infrastructure.fastapi.errors.handlers import (
    global_exception_handler,
    http_exception_handler,
)
from src.infrastructure.fastapi.middleware.request_id import request_id_middleware
from src.infrastructure.fastapi.middleware.trailing_slash import TrailingSlashMiddleware
from src.infrastructure.fastapi.routes.cart import router as carrito_router
from src.infrastructure.fastapi.routes.customization import router as personalizacion_router
from src.infrastructure.fastapi.routes.infrastructure import router as infraestructura_router
from src.infrastructure.fastapi.routes.pages import router as paginas_router
from src.infrastructure.fastapi.routes.quote import router as presupuesto_router
from src.infrastructure.fastapi.routes.seo import router as seo_router
from src.infrastructure.pyyaml.loaders import cargar_site
from src.infrastructure.structlog.logger import configurar_logging, get_logger

configurar_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida los archivos YAML antes de arrancar la Web Pública."""
    import httpx

    logger.info("web_publica.lifespan.start", message="Validando site.yml...")
    cargar_site()
    logger.info("web_publica.lifespan.site_ok", message="site.yml validado correctamente.")

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=10.0)
    logger.info("web_publica.lifespan.http_client_ok")
    yield

    await app.state.http_client.aclose()
    logger.info("web_publica.lifespan.stop")


app_web = FastAPI(title=f"{APP_TITLE} Web Pública", lifespan=lifespan, redirect_slashes=False)
app_web.add_middleware(GZipMiddleware, minimum_size=1000)
app_web.add_middleware(TrailingSlashMiddleware)
app_web.middleware("http")(request_id_middleware)
app_web.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app_web.add_exception_handler(Exception, global_exception_handler)

_BASE_DIR = Path(__file__).resolve().parents[3]
_STATIC_DIR = _BASE_DIR / "static" if (_BASE_DIR / "static").exists() else Path("static").resolve()

app_web.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


app_web.include_router(infraestructura_router)
app_web.include_router(paginas_router)
app_web.include_router(carrito_router)
app_web.include_router(presupuesto_router)
app_web.include_router(seo_router)
app_web.include_router(personalizacion_router)

# Alias para compatibilidad
app = app_web
