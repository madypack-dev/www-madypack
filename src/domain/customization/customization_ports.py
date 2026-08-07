"""Puertos de servicio para el Bounded Context de Personalización."""

from abc import ABC, abstractmethod
from src.domain.customization.customization import PersonalizacionBolsa


class IGeneradorFotopolimeroSVG(ABC):
    """Puerto para la generación del SVG vectorial monocromático de fotopolímero industrial."""

    @abstractmethod
    def generar_svg_fotopolimero(self, personalizacion: PersonalizacionBolsa) -> str:
        """Genera el contenido XML del SVG de fotopolímero en blanco y negro (cliché)."""
        pass


class IGeneradorMockupBolsaSVG(ABC):
    """Puerto para la generación del mockup 2D en SVG simulando la bolsa terminada."""

    @abstractmethod
    def generar_svg_mockup(self, personalizacion: PersonalizacionBolsa) -> str:
        """Genera el contenido XML del SVG con la previsualización realista 2D de la bolsa."""
        pass
