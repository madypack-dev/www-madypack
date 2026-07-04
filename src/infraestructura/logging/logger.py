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

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True) if sys.stdout.isatty() else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(nombre: str = "madypack"):
    """Devuelve un logger estructurado compatible."""
    return structlog.get_logger(nombre)
