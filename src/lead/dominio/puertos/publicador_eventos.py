from abc import ABC, abstractmethod
from src.lead.dominio.modelos.eventos import LeadCreado

class IPublicadorEventos(ABC):
    """Interfaz del puerto publicador de eventos."""
    
    @abstractmethod
    async def publicar_lead_creado(self, evento: LeadCreado) -> None:
        """Emite el evento de dominio LeadCreado."""
        pass
