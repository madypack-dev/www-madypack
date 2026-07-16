"""Proveedor de IPC neutro que siempre devuelve factor 1.0."""

from datetime import date
from decimal import Decimal

from src.domain.pricing.proveedor_ipc import IProveedorIPC


class ProveedorIPCDefault(IProveedorIPC):
    """Proveedor de respaldo que no aplica actualización inflacionaria.

    Útil para arranques sin datos IPC y para tests que no requieren
    actualización temporal.
    """

    def obtener_factor(self, desde: date, hasta: date) -> Decimal:
        return Decimal("1")
