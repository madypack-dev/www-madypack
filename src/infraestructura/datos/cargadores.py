"""Cargadores de archivos YAML parametrizados por tenant.

Los datos se organizan en carpetas bajo ``data/<tenant>/``.
Si no se encuentra el archivo para un tenant específico, se intenta
con el tenant por defecto como fallback.
"""

from pathlib import Path
from typing import Any

import yaml  # type: ignore

from src.infraestructura.config import FALLBACK_TENANT
from src.infraestructura.logging import get_logger

logger = get_logger()

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _path_yaml(tenant: str, nombre: str) -> Path:
    return DATA_DIR / tenant / nombre


def _cargar_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        logger.error(f"Error leyendo {path}: {exc}", exc_info=True)
        return None


def _cargar_con_fallback(tenant: str, nombre: str) -> Any:
    contenido = _cargar_yaml(_path_yaml(tenant, nombre))
    if contenido is None and tenant != FALLBACK_TENANT:
        logger.warning(
            f"No se encontró {nombre} para tenant '{tenant}', usando fallback '{FALLBACK_TENANT}'"
        )
        contenido = _cargar_yaml(_path_yaml(FALLBACK_TENANT, nombre))
    return contenido


def cargar_site(tenant: str) -> dict[str, Any]:
    """Carga ``site.yml`` para el tenant indicado."""
    contenido = _cargar_con_fallback(tenant, "site.yml")
    return contenido if isinstance(contenido, dict) else {}


def cargar_carrito_defecto(tenant: str) -> list[dict[str, Any]]:
    """Carga el catálogo por defecto (``carrito_defecto.yml``) del tenant."""
    contenido = _cargar_con_fallback(tenant, "carrito_defecto.yml")
    if not isinstance(contenido, dict):
        return []
    return contenido.get("articulos", [])


def cargar_tarifas(tenant: str) -> dict[str, Any]:
    """Carga ``tarifas.yml`` para el tenant indicado."""
    contenido = _cargar_con_fallback(tenant, "tarifas.yml")
    return contenido if isinstance(contenido, dict) else {}
