"""Motor genérico de cálculo de precios a partir de conceptos de tarifa."""

from src.domain.comercio.modelos.carrito import CalculoArticulo


def _estrategia_suma_por_unidad(
    calculo: CalculoArticulo, conceptos: dict[str, float], cantidad: int
) -> float:
    """Suma los conceptos indicados y multiplica por la cantidad."""
    unitario = sum(conceptos.get(concepto, 0.0) for concepto in calculo.conceptos)
    return unitario * cantidad


def _estrategia_suma_por_unidad_mas_fijo(
    calculo: CalculoArticulo, conceptos: dict[str, float], cantidad: int
) -> float:
    """Suma los conceptos indicados, multiplica por cantidad y suma un costo fijo."""
    unitario = sum(conceptos.get(concepto, 0.0) for concepto in calculo.conceptos)
    fijo = conceptos.get(calculo.concepto_fijo, 0.0) if calculo.concepto_fijo else 0.0
    return (unitario * cantidad) + fijo


class CalculadorPrecio:
    """Calcula precios estimados usando estrategias predefinidas."""

    _estrategias = {
        "suma_por_unidad": _estrategia_suma_por_unidad,
        "suma_por_unidad_mas_fijo": _estrategia_suma_por_unidad_mas_fijo,
    }

    def calcular(
        self, calculo: CalculoArticulo | None, conceptos: dict[str, float], cantidad: int
    ) -> float:
        """Devuelve el precio estimado para un artículo dado su configuración de cálculo."""
        if calculo is None:
            raise ValueError("El artículo no tiene configuración de cálculo.")

        estrategia = self._estrategias.get(calculo.tipo)
        if estrategia is None:
            raise ValueError(f"Tipo de cálculo desconocido: {calculo.tipo}")

        return estrategia(calculo, conceptos, cantidad)
