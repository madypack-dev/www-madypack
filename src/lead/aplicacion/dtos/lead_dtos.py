from pydantic import BaseModel, EmailStr, field_validator

class CrearLeadRequest(BaseModel):
    """Esquema de validación para los datos enviados desde el formulario."""
    nombre: str
    empresa: str
    telefono: str
    email: EmailStr

    @field_validator("telefono")
    @classmethod
    def normalizar_telefono_e164(cls, v: str) -> str:
        """Asegura que el número comience con '+' y cumpla el formato E.164."""
        # Limpiar caracteres no deseados
        clean = "".join(c for c in v if c.isdigit() or c == "+")
        if not clean:
            raise ValueError("El teléfono no contiene dígitos válidos.")
        
        # Formatear a formato internacional E.164 (default Argentina +54)
        if not clean.startswith("+"):
            if clean.startswith("54"):
                clean = "+" + clean
            else:
                # Si no tiene 54, asumimos Argentina.
                # Si el usuario ingresa celular tipo "11...", Chatwoot requiere el '9' internacional: +54 9 11 ...
                if clean.startswith("9"):
                    clean = "+54" + clean
                else:
                    clean = "+549" + clean
        return clean

class ConfirmacionPresupuestoResponse(BaseModel):
    """Respuesta estructurada para renderizar en la vista de confirmación."""
    lead_id: str
    codigo_referencia: str
    whatsapp_url: str
    pdf_url: str
