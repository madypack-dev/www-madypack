from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from src.infrastructure.config.settings import APP_TITLE
from src.infrastructure.datos.cargadores import (
    cargar_site,
    cargar_productos_tienda,
    cargar_tarifas,
)
from src.infrastructure.errores.handlers import global_exception_handler
from src.infrastructure.logging.logger import configurar_logging, get_logger
from src.infrastructure.middleware.request_id import request_id_middleware
from src.infrastructure.middleware.trailing_slash import TrailingSlashMiddleware
from src.infrastructure.rutas.carrito import router as carrito_router
from src.infrastructure.rutas.infraestructura import router as infraestructura_router
from src.infrastructure.rutas.paginas import router as paginas_router
from src.infrastructure.rutas.presupuesto import router as presupuesto_router

configurar_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida los archivos YAML antes de arrancar."""
    import httpx

    logger.info("Validando archivos YAML...")
    cargar_site()
    cargar_productos_tienda()
    cargar_tarifas()
    logger.info("Archivos YAML validados correctamente.")

    # Inicializar cliente HTTP singleton con límites del pool para reutilizar sockets TCP/TLS
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=10.0)
    logger.info("Cliente HTTP singleton inicializado en el state de la aplicación.")
    yield

    # Cerrar cliente HTTP de forma limpia en el apagado
    await app.state.http_client.aclose()
    logger.info("Cliente HTTP singleton cerrado correctamente.")


app = FastAPI(title=APP_TITLE, lifespan=lifespan, redirect_slashes=False)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrailingSlashMiddleware)
app.middleware("http")(request_id_middleware)
app.add_exception_handler(Exception, global_exception_handler)

# Servir archivos estáticos directamente desde static/
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(infraestructura_router)
app.include_router(paginas_router)
app.include_router(carrito_router)
app.include_router(presupuesto_router)
