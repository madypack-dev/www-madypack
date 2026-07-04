"""Configuración centralizada del logging.

Replica el formato de Uvicorn para mantener consistencia visual en los logs.
"""

import logging
import sys

from src.infraestructura.config.settings import LOG_LEVEL


def configurar_logging() -> None:
    """Configura el logger de la aplicación con el mismo formato de Uvicorn."""
    logger = logging.getLogger("madypack")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))

    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(nombre: str = "madypack") -> logging.Logger:
    """Devuelve un logger configurado.

    Permite inyectar logging en componentes sin acoplarse a un logger global.
    """
    return logging.getLogger(nombre)
