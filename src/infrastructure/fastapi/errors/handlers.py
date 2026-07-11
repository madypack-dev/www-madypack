"""Handlers globales de excepciones."""

from fastapi import Request
from fastapi.responses import HTMLResponse

from src.infrastructure.structlog.logger import get_logger

logger = get_logger()


async def global_exception_handler(request: Request, exc: Exception):
    """Retorna una página de error genérica ante excepciones no manejadas."""
    logger.exception("Excepción no manejada en el request", error=str(exc))
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Error en el Servidor | Madypack</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; color: #333; }
            h1 { color: #2853A1; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>Ha ocurrido un error inesperado</h1>
        <p>Nuestro equipo técnico ha sido notificado. Por favor, intente nuevamente más tarde.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=500)
