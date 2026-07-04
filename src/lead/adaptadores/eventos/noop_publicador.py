from src.lead.dominio.puertos.publicador_eventos import IPublicadorEventos
from src.lead.dominio.modelos.eventos import LeadCreado

class NoOpPublicador(IPublicadorEventos):
    """Adaptador temporal No-Op para desvincular el bróker de eventos."""
    
    async def publicar_lead_creado(self, evento: LeadCreado) -> None:
        """No realiza ninguna acción."""
        pass
