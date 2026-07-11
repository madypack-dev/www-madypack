from abc import ABC, abstractmethod
from src.domain.quote.quote import Presupuesto

class IQuoteRepository(ABC):
    """Interfaz (puerto) para la persistencia del agregado Presupuesto."""

    @abstractmethod
    def guardar(self, ref: str, presupuesto: Presupuesto) -> None:
        """Guarda un presupuesto indexado por su código de referencia."""
        pass

    @abstractmethod
    def obtener_por_referencia(self, ref: str) -> Presupuesto | None:
        """Recupera un presupuesto a partir de su código de referencia."""
        pass
