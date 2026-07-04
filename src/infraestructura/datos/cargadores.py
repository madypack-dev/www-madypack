"""Cargadores de archivos YAML parametrizados por tenant.

Los datos se organizan en carpetas bajo ``data/<tenant>/``.
Si no se encuentra el archivo para un tenant específico, se intenta
con el tenant por defecto como fallback.
"""

from pathlib import Path

import yaml  # type: ignore
from pydantic import ValidationError

from src.infraestructura.config.settings import FALLBACK_TENANT
from src.infraestructura.datos.modelos import CatalogoConfig, SiteConfig
from src.infraestructura.logging.logger import get_logger
from src.precios.dominio.modelos.tarifas import ConfiguracionTarifas

logger = get_logger()

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _path_yaml(tenant: str, nombre: str) -> Path:
    return DATA_DIR / tenant / nombre


def _cargar_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        contenido = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        logger.error(f"Error leyendo {path}: {exc}", exc_info=True)
        raise ValueError(f"Error leyendo {path}: {exc}") from exc

    if contenido is None:
        raise ValueError(f"El archivo {path} está vacío o no es YAML válido.")

    if not isinstance(contenido, (dict, list)):
        raise ValueError(f"El archivo {path} no contiene un diccionario o lista raíz válido.")

    return contenido


def _cargar_con_fallback(tenant: str, nombre: str) -> dict | list:
    contenido = _cargar_yaml(_path_yaml(tenant, nombre))
    if contenido is None and tenant != FALLBACK_TENANT:
        logger.warning(
            f"No se encontró {nombre} para tenant '{tenant}', usando fallback '{FALLBACK_TENANT}'"
        )
        contenido = _cargar_yaml(_path_yaml(FALLBACK_TENANT, nombre))

    if contenido is None:
        raise FileNotFoundError(
            f"No se encontró {nombre} ni para tenant '{tenant}' ni para fallback '{FALLBACK_TENANT}'."
        )

    return contenido


def cargar_site(tenant: str) -> SiteConfig:
    """Carga y valida ``site.yml`` para el tenant indicado."""
    contenido = _cargar_con_fallback(tenant, "site.yml")
    if not isinstance(contenido, dict):
        raise ValueError(f"site.yml para tenant '{tenant}' debe ser un diccionario.")
    try:
        return SiteConfig(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando site.yml para tenant '{tenant}': {exc}")
        raise


def cargar_productos_tienda(tenant: str) -> CatalogoConfig:
    """Carga y valida el catálogo de productos (``productos_tienda.yml``) del tenant."""
    contenido = _cargar_con_fallback(tenant, "productos_tienda.yml")
    if not isinstance(contenido, dict):
        raise ValueError(f"productos_tienda.yml para tenant '{tenant}' debe ser un diccionario.")
    try:
        return CatalogoConfig(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando productos_tienda.yml para tenant '{tenant}': {exc}")
        raise


def cargar_tarifas(tenant: str) -> ConfiguracionTarifas:
    """Carga y valida ``tarifas.yml`` para el tenant indicado."""
    contenido = _cargar_con_fallback(tenant, "tarifas.yml")
    if not isinstance(contenido, dict):
        raise ValueError(f"tarifas.yml para tenant '{tenant}' debe ser un diccionario.")
    try:
        return ConfiguracionTarifas(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando tarifas.yml para tenant '{tenant}': {exc}")
        raise
