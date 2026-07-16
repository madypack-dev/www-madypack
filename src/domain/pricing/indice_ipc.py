"""Value objects para modelar el índice de precios al consumidor (IPC)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class IndiceIPC(BaseModel):
    """Variación intermensual del IPC para un mes específico."""

    model_config = {"frozen": True}

    mes: date = Field(..., description="Primer día del mes al que corresponde el índice")
    variacion_intermensual: Decimal = Field(
        ...,
        ge=Decimal("-1"),
        description="Variación porcentual intermensual (ej. 0.15 para 15%)",
    )

    @field_validator("mes")
    @classmethod
    def _validar_primer_dia_del_mes(cls, valor: date) -> date:
        if valor.day != 1:
            raise ValueError("El mes de un índice IPC debe ser el primer día del mes.")
        return valor


class FactorIPC(BaseModel):
    """Factor acumulado de actualización a una fecha de vigencia."""

    model_config = {"frozen": True}

    valor: Decimal = Field(..., gt=0, description="Factor acumulado (ej. 1.322)")
    fecha: date = Field(..., description="Fecha de vigencia del factor")
