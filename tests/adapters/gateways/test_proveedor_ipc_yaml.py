"""Tests para el proveedor de IPC desde YAML."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.adapters.gateways.proveedor_ipc_yaml import ProveedorIPCYaml


@pytest.fixture
def archivo_ipc(tmp_path):
    ruta = tmp_path / "ipc.yml"
    ruta.write_text(
        """
ipc:
  - mes: "2024-01-01"
    variacion_intermensual: 0.10
  - mes: "2024-02-01"
    variacion_intermensual: 0.20
  - mes: "2024-03-01"
    variacion_intermensual: 0.05
""",
        encoding="utf-8",
    )
    return ruta


class TestProveedorIPCYaml:
    def test_factor_acumulado_correcto(self, archivo_ipc):
        proveedor = ProveedorIPCYaml(str(archivo_ipc))

        factor = proveedor.obtener_factor(date(2024, 1, 1), date(2024, 3, 1))

        # Se incluyen febrero y marzo (el mes de referencia enero se excluye)
        assert factor == Decimal("1.20") * Decimal("1.05")

    def test_factor_uno_si_no_hay_indices(self, archivo_ipc):
        proveedor = ProveedorIPCYaml(str(archivo_ipc))

        factor = proveedor.obtener_factor(date(2024, 1, 1), date(2024, 1, 1))

        assert factor == Decimal("1")

    def test_factor_uno_si_archivo_no_existe(self, tmp_path):
        ruta_inexistente = tmp_path / "no_existe.yml"
        proveedor = ProveedorIPCYaml(str(ruta_inexistente))

        factor = proveedor.obtener_factor(date(2024, 1, 1), date(2024, 6, 1))

        assert factor == Decimal("1")

    def test_no_incluye_mes_igual_a_desde(self, archivo_ipc):
        proveedor = ProveedorIPCYaml(str(archivo_ipc))

        factor = proveedor.obtener_factor(date(2024, 1, 1), date(2024, 2, 1))

        # Solo se incluye febrero (enero es el mes de referencia)
        assert factor == Decimal("1.20")

    def test_incluye_mes_igual_a_hasta(self, archivo_ipc):
        proveedor = ProveedorIPCYaml(str(archivo_ipc))

        factor = proveedor.obtener_factor(date(2023, 12, 1), date(2024, 1, 1))

        assert factor == Decimal("1.10")
