"""Modelos de dominio para la configuración genérica de tarifas."""

from pydantic import BaseModel, Field


class Tarifas(BaseModel):
    """Conjunto genérico de conceptos de costo indexados por nombre.

    Cada sitio define los conceptos que necesite para calcular precios.
    Ejemplos: base, manija_plana, manija_cordon, personalizacion, fijo_matriz.
    """

    conceptos: dict[str, float] = Field(default_factory=dict)


class ConfiguracionTarifas(BaseModel):
    """Raíz del archivo tarifas.yml."""

    tarifas: Tarifas
