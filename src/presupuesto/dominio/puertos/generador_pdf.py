"""Puerto de dominio para la generación del documento PDF de presupuesto."""

from abc import ABC, abstractmethod

from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import Presupuesto


class IGeneradorDocumentoPresupuesto(ABC):
    """Contrato que debe implementar cualquier generador de PDFs de presupuesto."""

    @abstractmethod
    def generar(self, presupuesto: Presupuesto, identidad_visual: IdentidadVisual) -> bytes:
        """Genera y devuelve el contenido binario del PDF."""
        ...
