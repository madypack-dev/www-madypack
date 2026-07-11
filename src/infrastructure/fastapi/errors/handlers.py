"""Handlers globales de excepciones y errores HTTP."""

from pathlib import Path

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from src.infrastructure.structlog.logger import get_logger

logger = get_logger()

TEMPLATE_500 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "500.html"
CSS_500 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "500.css"

TEMPLATE_404 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "404.html"
CSS_404 = Path(__file__).resolve().parents[4] / "templates" / "errors" / "404.css"


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


async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        logger.warning("Página no encontrada", path=request.url.path)
        try:
            html_content = TEMPLATE_404.read_text(encoding="utf-8")
            try:
                css_content = CSS_404.read_text(encoding="utf-8")
                html_content = html_content.replace("/* STYLES */", css_content)
            except Exception as css_err:
                logger.error(f"No se pudo leer el archivo CSS de error 404: {css_err}")
        except Exception as read_err:
            logger.error(f"No se pudo leer el template de error 404: {read_err}")
            html_content = "<h1>404 - Página no encontrada</h1><p>El recurso solicitado no existe.</p>"
        return HTMLResponse(content=html_content, status_code=404)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
