"""Modelos de dominio del agregado Presupuesto."""

from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class DatosSolicitante(BaseModel):
    """Value object con los datos del solicitante capturados en el formulario."""

    model_config = {"frozen": True}

    nombre: str | None = None
    email: EmailStr
    telefono: str
    empresa: str | None = None
    mensaje: str | None = None


class LineaPresupuesto(BaseModel):
    """Value object que representa una línea del presupuesto."""

    model_config = {"frozen": True}

    id_articulo: int
    nombre: str
    descripcion: str
    cantidad: int = Field(..., ge=100)
    precio_unitario_estimado: float = Field(..., ge=0)
    subtotal: float = Field(..., ge=0)
    unidad: str = Field(default="unidades")


    @field_validator("cantidad")
    @classmethod
    def validar_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad debe ser múltiplo de 100.")
        return valor


class Presupuesto(BaseModel):
    """Entidad raíz del agregado Presupuesto."""

    fecha_emision: date
    validez_dias: int = Field(..., ge=1)
    datos_solicitante: DatosSolicitante
    lineas: list[LineaPresupuesto]
    condiciones_comerciales: list[str]
    total_estimado: float = Field(..., ge=0)
