"""Configuración centralizada del logging.

Replica el formato de Uvicorn para mantener consistencia visual en los logs.
"""

import logging
import os
import sys
import structlog

from src.infrastructure.config.settings import LOG_LEVEL


def formateador_consola_uvicorn(logger, method_name, event_dict):
    """Procesador de renderizado para consola que replica el formato limpio de Uvicorn."""
    level = method_name.upper()
    level_padded = f"{level}:".ljust(10)
    
    event = event_dict.get("event", "")
    
    # Extraer variables de contexto extra
    extras = []
    for k, v in event_dict.items():
        if k not in ("event", "level", "timestamp", "logger", "request_id"):
            extras.append(f"{k}={v}")
            
    context = f" | {' '.join(extras)}" if extras else ""
    return f"{level_padded}{event}{context}"


def configurar_logging() -> None:
    """Configura structlog para proveer logging estructurado compatible con Uvicorn."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    )

    usar_json = (
        not sys.stdout.isatty()
        or os.getenv("LOG_FORMAT") == "json"
        or os.getenv("ENV") == "production"
    )
    renderer = structlog.processors.JSONRenderer() if usar_json else formateador_consola_uvicorn

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(nombre: str = "madypack"):
    """Devuelve un logger estructurado compatible."""
    return structlog.get_logger(nombre)
