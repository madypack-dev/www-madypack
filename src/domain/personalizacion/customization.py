"""Entidades y Value Objects del Bounded Context de Personalización Visual e Impresión."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EspecificacionBolsa(BaseModel):
    """Value Object que representa la especificación técnica y estética de una bolsa personalizada."""

    model_config = {"frozen": True}

    ancho_cm: float = Field(..., gt=0, description="Ancho del frente de la bolsa en cm")
    alto_cm: float = Field(..., gt=0, description="Alto de la bolsa en cm")
    fuelle_cm: float = Field(..., ge=0, description="Fuelle/lateral de la bolsa en cm")
    color_papel: str = Field(default="#D2B48C", description="Color de papel (Kraft Marrón por defecto)")
    color_tinta: str = Field(default="#000000", description="Color Hex de impresión de tinta")
    tipo_manija: Literal["sin_manija", "manija_plana", "manija_retorcida"] = Field(
        default="manija_retorcida", description="Tipo de manija de la bolsa"
    )

    @field_validator("ancho_cm", "alto_cm")
    @classmethod
    def validar_dimensiones_minimas(cls, valor: float) -> float:
        if valor < 5.0:
            raise ValueError("Las dimensiones principales de la bolsa deben ser de al menos 5 cm.")
        return valor


class ImagenDiseno(BaseModel):
    """Value Object que encapsula los bytes del archivo de diseño o logo subido por el cliente."""

    model_config = {"frozen": True}

    contenido_bytes: bytes
    mime_type: str

    @field_validator("contenido_bytes")
    @classmethod
    def validar_no_vacio(cls, valor: bytes) -> bytes:
        if not valor or len(valor) == 0:
            raise ValueError("El archivo de diseño no puede estar vacío.")
        return valor


class PersonalizacionBolsa(BaseModel):
    """Aggregate Root que orquesta la especificación técnica de la bolsa y la imagen de marca."""

    model_config = {"frozen": True}

    especificacion: EspecificacionBolsa
    diseno: ImagenDiseno

    def calcular_area_util_impresion(self) -> tuple[float, float]:
        """Calcula el área máxima recomendable de impresión (ancho x alto en cm) dejando márgenes de seguridad."""
        margen_lateral_cm = 1.5
        margen_vertical_cm = 2.0

        ancho_util = max(1.0, self.especificacion.ancho_cm - (margen_lateral_cm * 2))
        alto_util = max(1.0, self.especificacion.alto_cm - (margen_vertical_cm * 2))
        return (ancho_util, alto_util)
