from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from src.application.erp.use_cases import CasoUsoVerificarConexionERP
from src.domain.erp.entities import EstadoConexionERP
from src.infrastructure.config.settings import APP_TITLE
from src.infrastructure.fastapi.dependencies import get_erp_gateway
from src.infrastructure.fastapi.errors.handlers import (
    global_exception_handler,
    http_exception_handler,
)
from src.infrastructure.fastapi.middleware.request_id import request_id_middleware
from src.infrastructure.fastapi.routes.xubio_replica import router as xubio_replica_router
from src.infrastructure.structlog.logger import configurar_logging, get_logger

configurar_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import httpx

    logger.info("erp_private.lifespan.start", message="Iniciando Servidor Privado ERP...")
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=10.0)
    logger.info("erp_private.lifespan.http_client_ok")
    yield

    await app.state.http_client.aclose()
    logger.info("erp_private.lifespan.stop")


app_erp = FastAPI(title=f"{APP_TITLE} Microservicio ERP Privado", lifespan=lifespan)
app_erp.middleware("http")(request_id_middleware)
app_erp.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app_erp.add_exception_handler(Exception, global_exception_handler)


@app_erp.get("/health", tags=["Salud"])
async def health_check():
    return {"status": "ok", "service": "erp_integracion_privado"}


@app_erp.get("/api/v1/erp/conexion", response_model=EstadoConexionERP, tags=["ERP"])
async def verificar_conexion_erp(erp_gateway=Depends(get_erp_gateway)):
    caso_uso = CasoUsoVerificarConexionERP(erp_gateway)
    return await caso_uso.ejecutar()


app_erp.include_router(xubio_replica_router)

# Alias
app_private = app_erp
