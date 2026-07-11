from typing import Callable
from src.domain.commerce.cart import ArticuloCarrito
from src.domain.pricing.calculator import CalculadorPrecio

# Conceptos de costo estáticos (tarifas) en pesos
TARIFAS = {
    "base": 0.15,
    "manija_plana": 0.35,
    "manija_cordon": 0.65,
    "personalizacion": 0.20,
    "fijo_matriz": 1500.00,
}


class CotizadorServicio:
    """Servicio que calcula los precios estimados utilizando tarifas estáticas en código."""

    def __init__(
        self,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.registrar_error = registrar_error
        self._calculador = CalculadorPrecio()
        self._conceptos = TARIFAS

    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        try:
            return self._calculador.calcular(
                articulo.calculo, self._conceptos, articulo.cantidad
            )
        except Exception as err:
            self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            raise
