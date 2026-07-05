"""Configuración centralizada del logging.

Replica el formato de Uvicorn para mantener consistencia visual en los logs.
"""

import logging
import sys
import structlog

from src.infraestructura.config.settings import LOG_LEVEL


def configurar_logging() -> None:
    """Configura structlog para proveer logging estructurado tanto en desarrollo como en producción."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    )

    import os
    usar_json = (
        not sys.stdout.isatty()
        or os.getenv("LOG_FORMAT") == "json"
        or os.getenv("ENV") == "production"
    )
    renderer = structlog.processors.JSONRenderer() if usar_json else structlog.dev.ConsoleRenderer(colors=True)

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
