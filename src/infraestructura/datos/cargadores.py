"""Cargadores de archivos YAML para Madypack.

Los datos se organizan directamente bajo la carpeta ``data/``.
"""

from pathlib import Path

import yaml  # type: ignore
from pydantic import ValidationError

from src.infraestructura.datos.modelos import CatalogoConfig, SiteConfig
from src.infraestructura.logging.logger import get_logger
from src.precios.dominio.modelos.tarifas import ConfiguracionTarifas

logger = get_logger()

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _cargar_yaml(path: Path) -> dict | list:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
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


def cargar_site() -> SiteConfig:
    """Carga y valida ``site.yml``."""
    contenido = _cargar_yaml(DATA_DIR / "site.yml")
    if not isinstance(contenido, dict):
        raise ValueError("site.yml debe ser un diccionario.")
    try:
        return SiteConfig(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando site.yml: {exc}")
        raise


def cargar_productos_tienda() -> CatalogoConfig:
    """Carga y valida el catálogo de productos (``productos_tienda.yml``)."""
    contenido = _cargar_yaml(DATA_DIR / "productos_tienda.yml")
    if not isinstance(contenido, dict):
        raise ValueError("productos_tienda.yml debe ser un diccionario.")
    try:
        return CatalogoConfig(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando productos_tienda.yml: {exc}")
        raise


def cargar_tarifas() -> ConfiguracionTarifas:
    """Carga y valida ``tarifas.yml``."""
    contenido = _cargar_yaml(DATA_DIR / "tarifas.yml")
    if not isinstance(contenido, dict):
        raise ValueError("tarifas.yml debe ser un diccionario.")
    try:
        return ConfiguracionTarifas(**contenido)
    except ValidationError as exc:
        logger.error(f"Error validando tarifas.yml: {exc}")
        raise
