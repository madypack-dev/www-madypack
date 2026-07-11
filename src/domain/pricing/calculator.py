"""Motor genérico de cálculo de precios a partir de conceptos de tarifa."""

from typing import Protocol


class IConfiguracionCalculo(Protocol):
    """Interfaz conceptual para la configuración de cálculo de un artículo.

    Permite que el motor de cálculo de precios no dependa directamente de
    los modelos del catálogo o carrito.
    """

    tipo: str
    conceptos: list[str]
    concepto_fijo: str | None


class IEstrategiaCalculoPrecio(Protocol):
    """Interfaz para las estrategias de cálculo de precios (Strategy Pattern)."""

    def calcular(
        self,
        calculo: IConfiguracionCalculo,
        conceptos: dict[str, float],
        cantidad: int,
    ) -> float:
        ...


class EstrategiaSumaPorUnidad:
    """Suma los conceptos indicados y multiplica por la cantidad."""

    def calcular(
        self,
        calculo: IConfiguracionCalculo,
        conceptos: dict[str, float],
        cantidad: int,
    ) -> float:
        unitario = sum(conceptos.get(concepto, 0.0) for concepto in calculo.conceptos)
        return unitario * cantidad


class EstrategiaSumaPorUnidadMasFijo:
    """Suma los conceptos indicados, multiplica por cantidad y suma un costo fijo."""

    def calcular(
        self,
        calculo: IConfiguracionCalculo,
        conceptos: dict[str, float],
        cantidad: int,
    ) -> float:
        unitario = sum(conceptos.get(concepto, 0.0) for concepto in calculo.conceptos)
        fijo = conceptos.get(calculo.concepto_fijo, 0.0) if calculo.concepto_fijo else 0.0
        return (unitario * cantidad) + fijo


class CalculadorPrecio:
    """Calcula precios estimados usando estrategias predefinidas o registradas dinámicamente."""

    _estrategias: dict[str, IEstrategiaCalculoPrecio] = {
        "suma_por_unidad": EstrategiaSumaPorUnidad(),
        "suma_por_unidad_mas_fijo": EstrategiaSumaPorUnidadMasFijo(),
    }

    @classmethod
    def registrar_estrategia(cls, nombre: str, estrategia: IEstrategiaCalculoPrecio) -> None:
        """Registra una nueva estrategia de cálculo de precios."""
        cls._estrategias[nombre] = estrategia

    def calcular(
        self,
        calculo: IConfiguracionCalculo | None,
        conceptos: dict[str, float],
        cantidad: int,
    ) -> float:
        """Devuelve el precio estimado para un artículo dado su configuración de cálculo."""
        if calculo is None:
            raise ValueError("El artículo no tiene configuración de cálculo.")

        estrategia = self._estrategias.get(calculo.tipo)
        if estrategia is None:
            raise ValueError(f"Tipo de cálculo desconocido: {calculo.tipo}")

        return estrategia.calcular(calculo, conceptos, cantidad)
