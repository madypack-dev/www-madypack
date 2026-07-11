from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.infrastructure.logging.logger import get_logger
from src.infrastructure.datos.cargadores import cargar_site
from src.infrastructure.datos.modelos import SiteConfig
from src.infrastructure.dependencias import get_repositorio_carrito

import subprocess

def _get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode("ascii").strip()
    except Exception:
        return "1.0.0"

COMMIT_HASH = _get_git_commit()
logger = get_logger()

def inject_cart_count(request: Request) -> dict:
    """Inyecta el contador de líneas del carrito de compras en el contexto global de Jinja2."""
    try:
        repositorio = get_repositorio_carrito(request)
        carrito = repositorio.obtener_carrito()
        return {"cart_count": carrito.total_lineas}
    except Exception:
        return {"cart_count": 0}


def inject_versioned_url_for(request: Request) -> dict:
    """Sobrescribe url_for para inyectar automáticamente ?v={commit} en los estáticos."""
    def versioned_url_for(name: str, **path_params):
        url = request.url_for(name, **path_params)
        if name == "static" and "path" in path_params:
            if "?" in str(url):
                return f"{url}&v={COMMIT_HASH}"
            return f"{url}?v={COMMIT_HASH}"
        return url
    return {"url_for": versioned_url_for}


templates = Jinja2Templates(
    directory="templates",
    context_processors=[inject_cart_count, inject_versioned_url_for]
)


def load_site() -> SiteConfig:
    """Dependency que carga y valida ``site.yml``."""
    return cargar_site()
