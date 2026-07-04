"""Modelos de dominio del catálogo de productos/servicios."""

from pydantic import BaseModel, Field, field_validator


class ArticuloCatalogo(BaseModel):
    """Representa un artículo disponible en el catálogo del tenant."""

    id: int
    nombre: str
    descripcion: str
    cantidad_por_defecto: int = Field(..., ge=100)
    imagen: str

    @field_validator("cantidad_por_defecto")
    @classmethod
    def validar_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad por defecto debe ser múltiplo de 100.")
        return valor
