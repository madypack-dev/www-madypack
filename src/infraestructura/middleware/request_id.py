"""Middleware que asigna un request id único y loguea cada petición."""

import time
import uuid

import structlog
from fastapi import Request

from src.infraestructura.logging.logger import get_logger

logger = get_logger()


async def request_id_middleware(request: Request, call_next):
    """Asigna un X-Request-ID, bindea contexto de structlog y loguea la petición."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
    )

    start_time = time.time()
    es_estatico = request.url.path.startswith("/static/")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        if not es_estatico:
            logger.info(
                "Petición HTTP procesada",
                http_method=request.method,
                http_path=request.url.path,
                http_status=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as err:
        process_time = time.time() - start_time
        logger.error(
            "Excepción durante el procesamiento de la petición HTTP",
            http_method=request.method,
            http_path=request.url.path,
            duration_ms=round(process_time * 1000, 2),
            error=str(err),
            exc_info=True,
        )
        raise err
