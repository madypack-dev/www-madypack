"""Value object que representa una tasa de cambio respecto al peso argentino."""

from datetime import date

from pydantic import BaseModel, Field


class TasaCambio(BaseModel):
    """Tasa de cambio para convertir USD a ARS.

    El valor indica cuántos pesos argentinos equivalen a un dólar estadounidense.
    """

    model_config = {"frozen": True}

    fecha: date = Field(..., description="Fecha de vigencia de la tasa")
    ars_por_usd: float = Field(..., gt=0, description="Pesos argentinos por cada USD")
    fuente: str = Field(default="", description="Fuente de la tasa, ej. BNA dólar billete venta")
