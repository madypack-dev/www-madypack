"""Proveedor de tasa de cambio default (paridad 1:1)."""

from datetime import date

from src.domain.pricing.proveedor_tasa_cambio import IProveedorTasaCambio
from src.domain.pricing.tasa_cambio import TasaCambio


class ProveedorTasaCambioDefault(IProveedorTasaCambio):
    """Proveedor de respaldo que asume paridad 1:1 entre USD y ARS.

    Permite que el cotizador funcione sin configuración de tasa cuando todos
    los conceptos están expresados en ARS. Si algún concepto está en USD,
    el valor queda igual en ARS (tasa 1.0), lo que facilita tests y arranques
    sin datos de mercado.
    """

    def obtener_tasa(self) -> TasaCambio:
        return TasaCambio(fecha=date.today(), ars_por_usd=1.0, fuente="default")
