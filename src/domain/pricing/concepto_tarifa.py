"""Value object que representa un concepto de costo con su moneda origen."""

from pydantic import BaseModel, Field

from src.domain.pricing.moneda import Moneda


class ConceptoTarifa(BaseModel):
    """Concepto de costo unitario expresado en una moneda origen.

    El cotizador puede combinar conceptos en ARS y USD. Antes de presentar
    el precio final al cliente, todos los conceptos se convierten a ARS
    mediante una ``TasaCambio``.
    """

    model_config = {"frozen": True}

    nombre: str = Field(..., description="Identificador del concepto")
    monto: float = Field(..., ge=0, description="Valor unitario en la moneda origen")
    moneda: Moneda = Field(default=Moneda.ARS, description="Moneda en la que está expresado el monto")
