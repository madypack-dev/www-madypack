from pydantic import BaseModel


class IdentidadVisual(BaseModel):
    """Value object con la identidad visual del tenant para documentos generados."""

    model_config = {"frozen": True}

    brand: str = "Madypack"
    tagline: str | None = "Bolsas de papel sustentables"
    logo_path: str | None = None
    color_primario_hex: str = "#1a1a1a"
    color_acento_hex: str = "#333333"
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    url: str | None = None
    whatsapp: str | None = None
