"""Entrypoint de compatibilidad para la aplicación FastAPI.

Delega la ejecución en src.infrastructure.fastapi.app_web_publica.
"""

from src.infrastructure.fastapi.app_web_publica import app_web as app

__all__ = ["app"]
