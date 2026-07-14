"""Modelos de dominio para el catálogo: bienes y servicios."""

import re
import unicodedata
from typing import Literal, Annotated

from pydantic import BaseModel, Field, field_validator

from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto


class ComponenteBien(BaseModel):
    """Componente de un bien, ya sea una variación de otro bien o un servicio."""

    model_config = {"frozen": True}

    tipo: Literal["variacion", "servicio"]
    referencia_id: int
    cantidad: int = Field(1, ge=1)
    nombre: str


class ProductoBien(BaseModel):
    """Bien comercializable: puede ser simple (sin componentes) o compuesto."""

    model_config = {"frozen": True}

    tipo: Literal["bien"]
    id: int
    nombre: str
    descripcion: str
    slug: str | None = None
    imagen: str
    atributos_posibles: dict[str, list[str]]
    variaciones: list[VariacionProducto]
    componentes: list[ComponenteBien] = []
    cantidad_por_defecto: int = Field(default=100, ge=100)
    visible: bool = False

    @property
    def es_compuesto(self) -> bool:
        return len(self.componentes) > 0

    @property
    def url_slug(self) -> str:
        if self.slug:
            return self.slug
        return _slugify(self.nombre)

    @property
    def imagen_principal(self) -> str:
        if self.variaciones:
            return self.variaciones[0].imagen
        return self.imagen


class ProductoServicio(BaseModel):
    """Servicio que se aplica dentro de un bien compuesto."""

    model_config = {"frozen": True}

    tipo: Literal["servicio"]
    id: int
    nombre: str
    descripcion: str
    slug: str | None = None
    imagen: str
    calculo: CalculoArticulo
    cantidad_por_defecto: int = Field(default=100, ge=100)
    visible: bool = False

    @property
    def url_slug(self) -> str:
        if self.slug:
            return self.slug
        return _slugify(self.nombre)

    @property
    def imagen_principal(self) -> str:
        return self.imagen


Producto = Annotated[
    ProductoBien | ProductoServicio,
    Field(discriminator="tipo"),
]


def _slugify(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s
