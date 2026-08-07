from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmpresaERP:
    """Entidad de dominio que representa los datos principales de la empresa en el ERP."""
    id: str
    nombre: str
    identificacion_tributaria: Optional[str] = None
    email: Optional[str] = None


@dataclass(frozen=True)
class EstadoConexionERP:
    """Value Object que representa el estado de conectividad con el ERP."""
    activo: bool
    mensaje: str
    proveedor: str = "Desconocido"
