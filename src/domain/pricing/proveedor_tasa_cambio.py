"""Puerto de dominio para obtener la tasa de cambio vigente."""

from typing import Protocol

from src.domain.pricing.tasa_cambio import TasaCambio


class IProveedorTasaCambio(Protocol):
    """Abstracción que provee la tasa de cambio USD/ARS vigente."""

    def obtener_tasa(self) -> TasaCambio:
        """Devuelve la tasa de cambio vigente con su fecha."""
        ...
