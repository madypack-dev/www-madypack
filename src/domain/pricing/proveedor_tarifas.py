"""Puerto de dominio para obtener el conjunto de tarifas de costos."""

from typing import Protocol

from src.domain.pricing.concepto_tarifa import ConceptoTarifa


class IProveedorTarifas(Protocol):
    """Abstracción que provee las tarifas nominales de costos del sistema."""

    def obtener_tarifas(self) -> dict[str, ConceptoTarifa]:
        """Devuelve un diccionario de conceptos de tarifa indexados por nombre."""
        ...
