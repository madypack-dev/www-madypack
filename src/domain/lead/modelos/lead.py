import secrets
import uuid
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
        return cls._crear_con_prefijo(nombre, empresa, telefono, email, "COT")

    @classmethod
    def crear_cotizacion_general(cls, nombre: str, empresa: str, telefono: str, email: EmailStr) -> "Lead":
        """Factory method para cotizaciones generales sin carrito."""
        return cls._crear_con_prefijo(nombre, empresa, telefono, email, "COT-GEN")

    @classmethod
    def crear_contacto(cls, nombre: str, empresa: str, telefono: str, email: EmailStr) -> "Lead":
        """Factory method para contactos institucionales."""
        return cls._crear_con_prefijo(nombre, empresa, telefono, email, "CON")

    @classmethod
    def crear_emergencia(cls, nombre: str, empresa: str, telefono: str, email: EmailStr) -> "Lead":
        """Factory method para leads generados ante una falla crítica del sistema."""
        sufijo = str(uuid.uuid4())[:8].upper()
        return cls(
            codigo_referencia=f"COT-ERR-{sufijo}",
            nombre=nombre,
            empresa=empresa,
            telefono=telefono,
            email=email,
        )

    @classmethod
    def _crear_con_prefijo(
        cls, nombre: str, empresa: str, telefono: str, email: EmailStr, prefijo: str
    ) -> "Lead":
        fecha_str = datetime.now().strftime("%Y%m%d")
        sufijo_aleatorio = secrets.token_hex(2).upper()  # 4 caracteres alfanuméricos en mayúsculas
        return cls(
            codigo_referencia=f"{prefijo}-{fecha_str}-{sufijo_aleatorio}",
            nombre=nombre,
            empresa=empresa,
            telefono=telefono,
            email=email,
        )
