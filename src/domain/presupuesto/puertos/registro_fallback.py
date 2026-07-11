"""Puerto de dominio para registrar leads que no pudieron persistirse."""

from abc import ABC, abstractmethod

from src.domain.lead.modelos.lead import Lead


class IRegistroFallbackLead(ABC):
    """Contrato para guardar un lead de contingencia ante fallas de infraestructura."""

    @abstractmethod
    def guardar(self, lead: Lead, error_msg: str) -> None:
        """Registra el lead junto con el mensaje de error."""
        ...
