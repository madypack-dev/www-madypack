"""Servicio de dominio que actualiza un Dinero a valor presente usando IPC."""

from datetime import date

from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.proveedor_ipc import IProveedorIPC


class ActualizadorIPC:
    """Aplica un factor IPC acumulativo para llevar un monto a valor presente.

    Solo actualiza montos en ARS. Las monedas extranjeras se consideran
    convertidas a su valor de cambio vigente, por lo que no se reescalan
    por IPC local.
    """

    def __init__(self, proveedor_ipc: IProveedorIPC):
        self._proveedor = proveedor_ipc

    def actualizar(self, dinero: Dinero, fecha_destino: date) -> Dinero:
        """Devuelve el dinero actualizado a ``fecha_destino`` en valor presente."""
        if dinero.moneda != Moneda.ARS:
            return dinero

        if dinero.fecha_referencia >= fecha_destino:
            return dinero

        factor = self._proveedor.obtener_factor(dinero.fecha_referencia, fecha_destino)
        return dinero.model_copy(update={"monto": dinero.monto * factor})
