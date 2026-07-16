"""Helpers puros para construir partes del catálogo."""

from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.manija import formato_manija_para_ancho

from .data import FormatoBolsa


def construir_sku_bolsa(
    codigo: str,
    color_inicial: str,
    manija_inicial: str,
    impresion_inicial: str,
) -> str:
    """Construye el SKU de una variación de bolsa."""
    return f"B-{codigo}-{color_inicial}-{manija_inicial}-{impresion_inicial}"


def calculo_articulo_para_bolsa(
    manija: str,
    impresion: str,
    formato: FormatoBolsa,
) -> CalculoArticulo:
    """Devuelve el cálculo de precio que corresponde a una combinación de bolsa."""
    conceptos = ["base"]
    concepto_fijo: str | None = None

    if manija == "Manija Cordón":
        formato_manija = formato_manija_para_ancho(formato.ancho)
        conceptos.append(f"manija_cordon_{formato_manija.largo_mm}")
    elif manija == "Manija Plana":
        conceptos.append("manija_plana")

    if "Impresa" in impresion:
        conceptos.append("personalizacion")
        concepto_fijo = "fijo_matriz"

    tipo = "suma_por_unidad_mas_fijo" if concepto_fijo else "suma_por_unidad"
    return CalculoArticulo(
        tipo=tipo,
        conceptos=conceptos,
        concepto_fijo=concepto_fijo,
    )


def moq_para_impresion(impresion: str) -> int:
    """Devuelve el MOQ según el tipo de impresión."""
    if "Lisa" in impresion:
        return 500
    if "1 o 2" in impresion:
        return 1000
    return 3000


def imagen_para_manija(manija: str) -> str:
    """Devuelve la imagen por defecto según el tipo de manija."""
    return "bolsas-sin-m.svg" if manija == "Sin Manija" else "bolsas-con-m.svg"


def _texto_manija(manija: str) -> str:
    """Convierte el atributo manija a texto para el título del producto."""
    if manija == "Manija Cordón":
        return "con Manija Cordón"
    return "sin Manija"


def _texto_impresion(impresion: str) -> str:
    """Convierte el atributo impresión a 'Lisa' o 'Impresa'."""
    if "Lisa" in impresion:
        return "Lisa"
    return "Impresa"


def construir_nombre_bolsa(
    formato: FormatoBolsa,
    color: str,
    manija: str,
    impresion: str,
    gramaje: str = "100g",
) -> str:
    """Construye el título normalizado de un producto de bolsa.

    Formato: Bolsa {medidas} {color} {con/sin manija} {Lisa/Impresa} {gramaje}
    """
    return (
        f"Bolsa {formato.medidas} {color} {_texto_manija(manija)} "
        f"{_texto_impresion(impresion)} {gramaje}"
    )
