"""Value object y reglas de dominio para manijas de papel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatoManija:
    """Formato de una manija cordón de papel kraft.

    El costo se deriva del peso de la tira de papel:
    ancho (cm) × largo (m) × gramaje (g/m²) / 1000.
    """

    largo_mm: int
    ancho_cm: float = 8.0
    gramaje: int = 100

    @property
    def peso_kg_por_unidad(self) -> float:
        """Devuelve los kg de papel necesarios para una manija."""
        ancho_m = self.ancho_cm / 100
        largo_m = self.largo_mm / 1000
        return ancho_m * largo_m * self.gramaje / 1000

    @property
    def etiqueta(self) -> str:
        return f"{self.largo_mm}mm"


def formato_manija_para_ancho(ancho_bolsa_cm: float) -> FormatoManija:
    """Selecciona el formato de manija cordón recomendado para un ancho de bolsa.

    Regla de negocio:
    - Bolsas hasta 125mm de ancho → manija 114mm.
    - Bolsas hasta 160mm de ancho → manija 152mm.
    - Bolsas mayores → manija 190mm.
    """
    if ancho_bolsa_cm <= 125:
        return FormatoManija(largo_mm=114)
    if ancho_bolsa_cm <= 160:
        return FormatoManija(largo_mm=152)
    return FormatoManija(largo_mm=190)
