"""Handlers globales de excepciones."""

from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

from src.infrastructure.structlog.logger import get_logger

logger = get_logger()

TEMPLATE_500 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "500.html"
CSS_500 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "500.css"

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Excepción no manejada en el request", error=str(exc))
    
    try:
        html_content = TEMPLATE_500.read_text(encoding="utf-8")
        try:
            css_content = CSS_500.read_text(encoding="utf-8")
            html_content = html_content.replace("/* STYLES */", css_content)
        except Exception as css_err:
            logger.error(f"No se pudo leer el archivo CSS de error 500: {css_err}")
    except Exception as read_err:
        logger.error(f"No se pudo leer el template de error 500: {read_err}")
        html_content = "<h1>Ha ocurrido un error inesperado</h1><p>Intente nuevamente más tarde.</p>"
        
    return HTMLResponse(content=html_content, status_code=500)
