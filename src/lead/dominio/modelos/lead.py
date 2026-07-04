import secrets
from datetime import datetime
from pydantic import BaseModel, EmailStr

class Lead(BaseModel):
    """Entidad de dominio Lead."""
    id: str | None = None  # ID de contacto devuelto por Chatwoot (nulo antes de persistir)
    codigo_referencia: str  # COT-YYYYMMDD-XXXX
    nombre: str
    empresa: str
    telefono: str  # Formato E.164
    email: EmailStr

    @classmethod
    def crear(cls, nombre: str, empresa: str, telefono: str, email: EmailStr) -> "Lead":
        """Factory method que genera el código de referencia único B2B y retorna la entidad Lead."""
        fecha_str = datetime.now().strftime("%Y%m%d")
        sufijo_aleatorio = secrets.token_hex(2).upper()  # Genera 4 caracteres alfanuméricos en mayúsculas
        codigo = f"COT-{fecha_str}-{sufijo_aleatorio}"
        
        return cls(
            codigo_referencia=codigo,
            nombre=nombre,
            empresa=empresa,
            telefono=telefono,
            email=email
        )
