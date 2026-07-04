"""Configuración centralizada del logging."""

import logging
import sys

from src.infraestructura.config.settings import LOG_LEVEL


def configurar_logging() -> None:
    """Configura el logging básico de la aplicación."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )


def get_logger(nombre: str = "madypack") -> logging.Logger:
    """Devuelve un logger configurado.

    Permite inyectar logging en componentes sin acoplarse a un logger global.
    """
    return logging.getLogger(nombre)
