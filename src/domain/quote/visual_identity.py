"""Value object con la identidad visual del emisor para el PDF."""

from pydantic import BaseModel


class IdentidadVisual(BaseModel):
    """Datos de identidad visual que aparecerán en el presupuesto."""

    model_config = {"frozen": True}

    brand: str
    tagline: str | None = None
    logo_path: str | None = None  # Path absoluto del archivo de logo en disco
    email: str
    telefono: str
    direccion: str
    whatsapp: str | None = None
    url: str | None = None

