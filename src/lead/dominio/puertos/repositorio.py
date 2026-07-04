from abc import ABC, abstractmethod
from src.lead.dominio.modelos.lead import Lead

class ILeadRepository(ABC):
    """Interfaz del puerto de persistencia del Lead."""
    
    @abstractmethod
    async def guardar(self, lead: Lead, inbox_id: int) -> str:
        """
        Envía el Lead a Chatwoot y retorna el ID del contacto creado.
        Si la API de Chatwoot falla, lanza una excepción.
        """
        pass

    @abstractmethod
    async def obtener_por_id(self, lead_id: str) -> Lead | None:
        """Obtiene un contacto de Chatwoot por su ID y lo mapea a la entidad Lead."""
        pass
