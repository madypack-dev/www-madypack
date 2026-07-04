"""Value object con la identidad visual del emisor (tenant) para el PDF."""

from pydantic import BaseModel


class IdentidadVisual(BaseModel):
    """Datos de identidad visual del tenant que aparecerán en el presupuesto."""

    brand: str
    tagline: str | None = None
    logo_path: str | None = None  # Path absoluto del archivo de logo en disco
    email: str
    telefono: str
    direccion: str
    whatsapp: str | None = None
    url: str | None = None
