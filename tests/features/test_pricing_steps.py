from datetime import date
from decimal import Decimal

from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.pricing.actualizador_ipc import ActualizadorIPC
from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.proveedor_ipc import IProveedorIPC

scenarios("pricing_ipc.feature")


class StubProveedorIPC(IProveedorIPC):
    def __init__(self, factor: Decimal):
        self.factor = factor

    def obtener_factor(self, fecha_desde: date, fecha_hasta: date) -> Decimal:
        return self.factor


@given(parsers.parse('un valor de tarifa base de {monto:f} ARS registrado en fecha "{fecha}"'), target_fixture="dinero_base")
def dinero_base(monto: float, fecha: str) -> Dinero:
    return Dinero(
        monto=Decimal(str(monto)),
        moneda=Moneda.ARS,
        fecha_referencia=date.fromisoformat(fecha)
    )


@given(parsers.parse('un factor IPC acumulado de {factor:f} hasta la fecha "{fecha_fin}"'), target_fixture="ipc_context")
def ipc_context(factor: float, fecha_fin: str) -> tuple[Decimal, date]:
    return Decimal(str(factor)), date.fromisoformat(fecha_fin)


@when("se calcula el importe actualizado a valor presente", target_fixture="monto_actualizado")
def calcular_monto_actualizado(dinero_base: Dinero, ipc_context: tuple[Decimal, date]) -> Dinero:
    factor, fecha_fin = ipc_context
    proveedor = StubProveedorIPC(factor)
    actualizador = ActualizadorIPC(proveedor_ipc=proveedor)
    return actualizador.actualizar(dinero_base, fecha_fin)


@then(parsers.parse('el precio unitario resultante debe ser {esperado:f} ARS'))
def verificar_precio_unitario(monto_actualizado: Dinero, esperado: float) -> None:
    assert monto_actualizado.monto == Decimal(str(esperado))
    assert monto_actualizado.moneda == Moneda.ARS
