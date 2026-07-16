"""Puerto de dominio para obtener el factor de actualización IPC."""

from datetime import date
from decimal import Decimal
from typing import Protocol


class IProveedorIPC(Protocol):
    """Abstracción que provee el factor IPC acumulado entre dos fechas."""

    def obtener_factor(self, desde: date, hasta: date) -> Decimal:
        """Devuelve el factor acumulado intermensual para actualizar montos en ARS.

        El factor representa cuánto se debe multiplicar un monto de ``desde``
        para expresarlo en valores de ``hasta``.
        """
        ...
