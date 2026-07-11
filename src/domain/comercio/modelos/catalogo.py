"""Modelos de dominio del catálogo de productos/servicios."""

import re
import unicodedata
from pydantic import BaseModel, Field, field_validator

from src.domain.comercio.modelos.carrito import CalculoArticulo


class ArticuloCatalogo(BaseModel):
    """Representa un artículo disponible en el catálogo."""

    model_config = {"frozen": True}

    id: int
    nombre: str
    descripcion: str
    cantidad_por_defecto: int = Field(..., ge=100)
    imagen: str
    calculo: CalculoArticulo | None = None
    slug: str | None = None


    @property
    def url_slug(self) -> str:
        if self.slug:
            return self.slug
        s = unicodedata.normalize('NFKD', self.nombre).encode('ascii', 'ignore').decode('utf-8')
        s = re.sub(r'[^\w\s-]', '', s).strip().lower()
        s = re.sub(r'[-\s]+', '-', s)
        return s

    @field_validator("cantidad_por_defecto")
    @classmethod
    def validar_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad por defecto debe ser múltiplo de 100.")
        return valor

