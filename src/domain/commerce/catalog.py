"""Modelos de dominio del catálogo de productos/servicios."""

from pydantic import BaseModel, Field, field_validator

from src.domain.commerce.cart import CalculoArticulo


class VariacionProducto(BaseModel):
    """Representa una variante específica de un producto simple."""

    model_config = {"frozen": True}

    id: int
    sku: str
    atributos: dict[str, str]  # Ej: {"color": "Marrón", "manija": "Sin Manija"}
    imagen: str
    cantidad_por_defecto: int = Field(1000, ge=100)
    calculo: CalculoArticulo | None = None

    @field_validator("cantidad_por_defecto")
    @classmethod
    def validar_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad por defecto debe ser múltiplo de 100.")
        return valor
