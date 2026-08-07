"""Caso de uso de aplicación para procesar la personalización de bolsa (Fotopolímero + Mockup)."""

from collections.abc import Callable
from dataclasses import dataclass

from src.domain.personalizacion.customization import (
    EspecificacionBolsa,
    ImagenDiseno,
    PersonalizacionBolsa,
)
from src.domain.personalizacion.customization_ports import (
    IGeneradorFotopolimeroSVG,
    IGeneradorMockupBolsaSVG,
)


@dataclass(frozen=True)
class SolicitudPersonalizacionDTO:
    ancho_cm: float
    alto_cm: float
    fuelle_cm: float
    color_papel: str
    color_tinta: str
    tipo_manija: str
    contenido_bytes: bytes
    mime_type: str


@dataclass(frozen=True)
class ResultadoPersonalizacionDTO:
    svg_fotopolimero: str
    svg_mockup: str
    especificacion: EspecificacionBolsa
    ancho_util_cm: float
    alto_util_cm: float


class CasoUsoGenerarPersonalizacion:
    """Caso de uso que valida la especificación y coordina los adaptadores de renderizado SVG."""

    def __init__(
        self,
        generador_fotopolimero: IGeneradorFotopolimeroSVG,
        generador_mockup: IGeneradorMockupBolsaSVG,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.generador_fotopolimero = generador_fotopolimero
        self.generador_mockup = generador_mockup
        self.registrar_error = registrar_error

    def ejecutar(self, solicitud: SolicitudPersonalizacionDTO) -> ResultadoPersonalizacionDTO:
        try:
            especificacion = EspecificacionBolsa(
                ancho_cm=solicitud.ancho_cm,
                alto_cm=solicitud.alto_cm,
                fuelle_cm=solicitud.fuelle_cm,
                color_papel=solicitud.color_papel,
                color_tinta=solicitud.color_tinta,
                tipo_manija=solicitud.tipo_manija,  # type: ignore
            )
            diseno = ImagenDiseno(
                contenido_bytes=solicitud.contenido_bytes,
                mime_type=solicitud.mime_type,
            )
            personalizacion = PersonalizacionBolsa(
                especificacion=especificacion,
                diseno=diseno,
            )
        except ValueError as err:
            self.registrar_error(f"Error de validación en solicitud de personalización: {err}")
            raise

        ancho_util, alto_util = personalizacion.calcular_area_util_impresion()

        svg_fotopolimero = self.generador_fotopolimero.generar_svg_fotopolimero(personalizacion)
        svg_mockup = self.generador_mockup.generar_svg_mockup(personalizacion)

        return ResultadoPersonalizacionDTO(
            svg_fotopolimero=svg_fotopolimero,
            svg_mockup=svg_mockup,
            especificacion=especificacion,
            ancho_util_cm=ancho_util,
            alto_util_cm=alto_util,
        )
