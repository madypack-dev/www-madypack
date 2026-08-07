"""Puerto de dominio para la generación del documento PDF de presupuesto."""

from abc import ABC, abstractmethod

from src.domain.quote.visual_identity import IdentidadVisual
from src.domain.quote.quote import Presupuesto


class IGeneradorDocumentoPresupuesto(ABC):
    """Contrato que debe implementar cualquier generador de PDFs de presupuesto."""

    @abstractmethod
    def generar(self, presupuesto: Presupuesto, identidad_visual: IdentidadVisual) -> bytes:
        """Genera y devuelve el contenido binario del PDF."""
        ...
