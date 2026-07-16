"""Tests para el servicio de dominio ActualizadorIPC."""

from datetime import date
from decimal import Decimal

from src.domain.pricing.actualizador_ipc import ActualizadorIPC
from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.proveedor_ipc import IProveedorIPC


class _ProveedorIPCFijo:
    def __init__(self, factor: Decimal):
        self._factor = factor

    def obtener_factor(self, desde: date, hasta: date) -> Decimal:
        return self._factor


class TestActualizadorIPC:
    def test_factor_uno_cuando_fechas_coinciden(self):
        proveedor = _ProveedorIPCFijo(Decimal("1.5"))
        actualizador = ActualizadorIPC(proveedor)
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 6, 1))

        resultado = actualizador.actualizar(dinero, date(2024, 6, 1))

        assert resultado.monto == Decimal("100")

    def test_actualiza_monto_ars_con_factor(self):
        proveedor = _ProveedorIPCFijo(Decimal("1.21"))
        actualizador = ActualizadorIPC(proveedor)
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

        resultado = actualizador.actualizar(dinero, date(2024, 6, 1))

        assert resultado.monto == Decimal("121")
        assert resultado.fecha_referencia == date(2024, 1, 1)
        assert resultado.moneda == Moneda.ARS

    def test_no_actualiza_si_fecha_referencia_es_posterior(self):
        proveedor = _ProveedorIPCFijo(Decimal("1.21"))
        actualizador = ActualizadorIPC(proveedor)
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 6, 1))

        resultado = actualizador.actualizar(dinero, date(2024, 1, 1))

        assert resultado.monto == Decimal("100")

    def test_no_actualiza_monedas_extranjeras(self):
        proveedor = _ProveedorIPCFijo(Decimal("1.21"))
        actualizador = ActualizadorIPC(proveedor)
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.USD, fecha_referencia=date(2024, 1, 1))

        resultado = actualizador.actualizar(dinero, date(2024, 6, 1))

        assert resultado.monto == Decimal("100")
        assert resultado.moneda == Moneda.USD

    def test_factor_menor_a_uno_reduce_monto(self):
        proveedor = _ProveedorIPCFijo(Decimal("0.90"))
        actualizador = ActualizadorIPC(proveedor)
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

        resultado = actualizador.actualizar(dinero, date(2024, 6, 1))

        assert resultado.monto == Decimal("90")
