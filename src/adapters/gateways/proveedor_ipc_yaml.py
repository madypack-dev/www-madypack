"""Proveedor de IPC que lee una tabla de índices mensuales desde YAML."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from src.domain.pricing.indice_ipc import IndiceIPC
from src.domain.pricing.proveedor_ipc import IProveedorIPC


class ProveedorIPCYaml(IProveedorIPC):
    """Lee índices IPC desde un archivo YAML y calcula el factor acumulado.

    Estructura esperada del YAML::

        ipc:
          - mes: "2024-01-01"
            variacion: 0.15
          - mes: "2024-02-01"
            variacion: 0.13
    """

    def __init__(self, ruta: str):
        self._ruta = Path(ruta)
        self._indices = self._cargar()

    def _cargar(self) -> list[IndiceIPC]:
        if not self._ruta.exists():
            return []

        import yaml

        with self._ruta.open(encoding="utf-8") as archivo:
            datos = yaml.safe_load(archivo) or {}

        return [IndiceIPC(**item) for item in datos.get("ipc", [])]

    def obtener_factor(self, desde: date, hasta: date) -> Decimal:
        """Devuelve el factor acumulado entre ``desde`` y ``hasta``.

        Solo considera índices cuyo mes sea estrictamente posterior a
        ``desde`` e igual o anterior a ``hasta``. Si ``desde`` es igual o
        posterior a ``hasta`` no hay actualización.
        """
        if desde >= hasta:
            return Decimal("1")

        indices_aplicables = [i for i in self._indices if desde < i.mes <= hasta]
        factor = Decimal("1")
        for indice in sorted(indices_aplicables, key=lambda i: i.mes):
            factor *= Decimal("1") + indice.variacion_intermensual
        return factor
