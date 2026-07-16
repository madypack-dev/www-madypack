"""Conversor de conceptos de tarifa a pesos argentinos."""

from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.tasa_cambio import TasaCambio


class ConversorMoneda:
    """Convierte un diccionario de conceptos de tarifa a valores en ARS."""

    def __init__(self, tasa: TasaCambio):
        self._tasa = tasa

    def convertir_conceptos(self, conceptos: dict[str, ConceptoTarifa]) -> dict[str, float]:
        """Devuelve un nuevo diccionario con cada concepto expresado en ARS."""
        return {nombre: self._a_ars(concepto) for nombre, concepto in conceptos.items()}

    def _a_ars(self, concepto: ConceptoTarifa) -> float:
        if concepto.moneda == Moneda.USD:
            return concepto.monto * self._tasa.ars_por_usd
        return concepto.monto
