from datetime import date
import time
from pathlib import Path
from typing import Callable

from fastapi import Request, Response, Depends
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates

from src.infraestructura.logging.logger import get_logger
from src.infraestructura.tenant.resolutor import resolutor_tenant
from src.infraestructura.datos.cargadores import cargar_site
from src.infraestructura.datos.modelos import SiteConfig
from src.infraestructura.tenant.resolutor import resolutor_tenant
from src.infraestructura.datos.cargadores import cargar_productos_tienda
from src.comercio.adaptadores.repositorios.cookie import RepositorioCarritoCookie

logger = get_logger()

def inject_cart_count(request: Request) -> dict:
    """Inyecta el contador de líneas del carrito de compras en el contexto global de Jinja2."""
    try:
        tenant = resolutor_tenant(request)
        repositorio = RepositorioCarritoCookie(
            cookies=request.cookies,
            cargar_productos_tienda=lambda: cargar_productos_tienda(tenant).articulos,
        )
        carrito = repositorio.obtener_carrito()
        return {"cart_count": carrito.total_lineas}
    except Exception:
        return {"cart_count": 0}


templates = Jinja2Templates(directory="templates", context_processors=[inject_cart_count])


def load_site(tenant: str = Depends(resolutor_tenant)) -> SiteConfig:
    """Dependency que carga y valida ``site.yml`` para el tenant resuelto del request."""
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
