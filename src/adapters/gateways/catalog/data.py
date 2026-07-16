"""Datos crudos y constantes para la construcción del catálogo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatoBolsa:
    """Datos crudos de un formato de bolsa de papel."""

    codigo: str
    medidas: str
    rubro: str

    @property
    def ancho(self) -> int:
        """Ancho de la bolsa en cm, extraído del código de formato."""
        return int(self.codigo[:2])


FORMATOS_BOLSA: list[FormatoBolsa] = [
    FormatoBolsa("120819", "12x8x19 cm", "para Farmacia y Joyería"),
    FormatoBolsa("120841", "12x8x41 cm", "para Vinos y Licores"),
    FormatoBolsa("161024", "16x10x24 cm", "para Delivery Chico y Cafetería"),
    FormatoBolsa("221030", "22x10x30 cm", "para Hamburguesas y Delivery"),
    FormatoBolsa("261236", "26x12x36 cm", "para Indumentaria y Tiendas"),
    FormatoBolsa("301241", "30x12x41 cm", "para Calzado y Abrigos"),
]

COLORES_BOLSA: list[tuple[str, str, str]] = [
    ("Marrón", "Kraft Marrón", "marron"),
    ("Blanco", "Blanca", "blanco"),
]

MANIJAS_BOLSA: list[tuple[str, str]] = [
    ("Sin Manija", "SOS"),
    ("Manija Cordón", "CRD"),
]

IMPRESIONES_BOLSA: list[tuple[str, str]] = [
    ("Lisa (sin impresión)", "L"),
    ("Impresa 1 o 2 colores", "I"),
    ("Impresa Cuatricromía", "C"),
]

ID_INICIAL_PRODUCTO_BOLSA = 1001
ID_INICIAL_VARIACION = 1
ID_INICIAL_COMPONENTE = 1101
ID_INICIAL_SERVICIO = 2001
# Rangos fijos para compuestos. Cada familia tiene un rango base estable para
# evitar que agregar un nuevo compuesto predefinido desplace los IDs de otras
# familias.
ID_BASE_COMPUESTOS_PREDEFINIDOS = 3001
ID_BASE_COMPUESTOS_CON_MANIJA = 3101
ID_BASE_COMPUESTOS_IMPRESOS = 3201
ID_BASE_COMPUESTOS_IMPRESOS_CON_MANIJA = 3301
ID_BASE_OTROS_COMPUESTOS = 3401

SLUG_BOLSA_VISIBLE_CON_MANIJA = "bolsa-de-papel-marron-221030-base"
SLUG_BOLSA_VISIBLE_IMPRESA_SIN_MANIJA = "bolsa-de-papel-impresa-marron-221030-base"
SLUG_BOLSA_VISIBLE_IMPRESA_CON_MANIJA = "bolsa-de-papel-impresa-marron-221030-base-con-manija-cordon"
