"""Value Object de Dominio para representar el Margen Comercial de Reventa."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MargenComercial:
    """Margen de ganancia común aplicado a la reventa de bienes y servicios.

    Atributos:
        porcentaje: Flotante que representa el porcentaje de margen (ej. 0.20 para 20%).
    """

    porcentaje: float = 0.20

    def __post_init__(self) -> None:
        if self.porcentaje < 0:
            raise ValueError("El porcentaje de margen comercial no puede ser negativo.")

    def aplicar(self, costo: float) -> float:
        """Aplica el margen comercial al costo base dado."""
        if costo < 0:
            raise ValueError("El costo base no puede ser negativo.")
        return costo * (1.0 + self.porcentaje)
