"""Value object que representa una cantidad de dinero con moneda y fecha de referencia."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.pricing.moneda import Moneda


class Dinero(BaseModel):
    """Cantidad monetaria con contexto temporal.

    El ``monto`` es nominal y está referenciado a ``fecha_referencia``.
    Para comparar o presentar montos en diferentes fechas se debe aplicar
    un factor de actualización (por ejemplo, IPC).
    """

    model_config = {"frozen": True}

    monto: Decimal = Field(..., ge=0, description="Monto nominal en la moneda indicada")
    moneda: Moneda = Field(..., description="Moneda del monto")
    fecha_referencia: date = Field(
        ...,
        description="Fecha a la que corresponde el valor nominal",
    )
