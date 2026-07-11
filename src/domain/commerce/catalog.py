"""Modelos de dominio del catálogo de productos/servicios."""

import re
import unicodedata
from pydantic import BaseModel, Field, field_validator
from src.domain.commerce.cart import CalculoArticulo


class VariacionProducto(BaseModel):
    """Representa una variante específica de un producto."""

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


class ProductoVariable(BaseModel):
    """Representa un producto variable con múltiples opciones y variantes."""

    model_config = {"frozen": True}

    id: int
    nombre: str
    descripcion: str  # Descripción base/general
    slug: str | None = None
    atributos_posibles: dict[str, list[str]]  # Ej: {"color": ["Marrón", "Blanco"], "manija": ["Sin Manija", "Cordón"]}
    variaciones: list[VariacionProducto]

    @property
    def url_slug(self) -> str:
        if self.slug:
            return self.slug
        s = unicodedata.normalize('NFKD', self.nombre).encode('ascii', 'ignore').decode('utf-8')
        s = re.sub(r'[^\w\s-]', '', s).strip().lower()
        s = re.sub(r'[-\s]+', '-', s)
        return s
