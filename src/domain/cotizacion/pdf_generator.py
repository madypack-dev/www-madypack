from abc import ABC, abstractmethod

from src.domain.cotizacion.quote import Presupuesto
from src.domain.cotizacion.visual_identity import IdentidadVisual


class IGeneradorDocumentoPresupuesto(ABC):
    """Puerto para la generación del documento formal de presupuesto (PDF)."""

    @abstractmethod
    def generar(self, presupuesto: Presupuesto, identidad_visual: IdentidadVisual) -> bytes:
        """Genera el contenido binario del documento de presupuesto (ej: PDF)."""
        pass
