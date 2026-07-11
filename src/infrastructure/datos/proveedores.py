"""Proveedores de datos compartidos entre rutas de infraestructura."""

from typing import Any

from src.domain.comercio.modelos.catalogo import ArticuloCatalogo
from src.infrastructure.datos.cargadores import cargar_productos_tienda, cargar_tarifas
from src.infrastructure.logging.logger import get_logger

logger = get_logger()


def obtener_productos_tienda() -> list[ArticuloCatalogo]:
    """Devuelve el catálogo validado o una lista vacía si hay error."""
    try:
        return cargar_productos_tienda().articulos
    except Exception as err:
        logger.error(f"Error obteniendo catálogo: {err}", exc_info=True)
        return []


def obtener_tarifas() -> dict[str, Any]:
    """Devuelve las tarifas validadas o un diccionario vacío si hay error."""
    try:
        return cargar_tarifas().model_dump()
    except Exception as err:
        logger.error(f"Error obteniendo tarifas: {err}", exc_info=True)
        return {}
