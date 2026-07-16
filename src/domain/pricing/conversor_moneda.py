"""Conversor de conceptos de tarifa a pesos argentinos."""

from decimal import Decimal

from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.tasa_cambio import TasaCambio


class ConversorMoneda:
    """Convierte un diccionario de conceptos de tarifa a valores en ARS."""

    def __init__(self, tasa: TasaCambio):
        self._tasa = tasa

    def convertir_conceptos(self, conceptos: dict[str, ConceptoTarifa]) -> dict[str, Dinero]:
        """Devuelve un nuevo diccionario con cada concepto expresado en ARS como Dinero."""
        return {nombre: self._a_dinero(concepto) for nombre, concepto in conceptos.items()}

    def _a_dinero(self, concepto: ConceptoTarifa) -> Dinero:
        monto = Decimal(str(concepto.monto))
        if concepto.moneda == Moneda.USD:
            return Dinero(
                monto=monto * Decimal(str(self._tasa.ars_por_usd)),
                moneda=Moneda.ARS,
                fecha_referencia=self._tasa.fecha,
            )
        return Dinero(
            monto=monto,
            moneda=Moneda.ARS,
            fecha_referencia=concepto.fecha,
        )
