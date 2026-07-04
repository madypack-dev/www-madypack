from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class LeadCreado(BaseModel):
    """Datos asociados al evento de dominio LeadCreado."""
    id_evento: UUID
    ocurrido_en: datetime
    lead_id: str  # ID de Chatwoot o fallback
    nombre: str
    empresa: str
    telefono: str
    email: str
    codigo_referencia: str
    resumen_lineas: int
