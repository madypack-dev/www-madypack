from datetime import date
import time
from pathlib import Path
from typing import Callable, Any

from fastapi import Request, Response, Depends
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates

from src.infraestructura.logging import get_logger
from src.infraestructura.tenant.resolutor import resolutor_tenant
from src.infraestructura.datos.cargadores import cargar_site

logger = get_logger()

templates = Jinja2Templates(directory="templates")


def load_site(tenant: str = Depends(resolutor_tenant)) -> dict[str, Any]:
    """Dependency que carga ``site.yml`` para el tenant resuelto del request."""
    return cargar_site(tenant)


class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            try:
                response: Response = await original_route_handler(request)
                duration = time.time() - start_time
                logger.info(
                    f"Method: {request.method} | Path: {request.url.path} | "
                    f"Status: {response.status_code} | Duration: {duration:.4f}s"
                )
                return response
            except Exception as exc:
                duration = time.time() - start_time
                logger.error(
                    f"EXCEPTION - Method: {request.method} | Path: {request.url.path} | "
                    f"Duration: {duration:.4f}s | Error: {str(exc)}",
                    exc_info=True
                )
                raise exc
                
        return custom_route_handler
