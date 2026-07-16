"""Builders para bolsas de papel simples y sus variaciones."""

from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import ProductoBien

from .builders import (
    calculo_articulo_para_bolsa,
    construir_sku_bolsa,
    imagen_para_manija,
    moq_para_impresion,
)
from .data import (
    COLORES_BOLSA,
    FORMATOS_BOLSA,
    FormatoBolsa,
    ID_INICIAL_PRODUCTO_BOLSA,
    ID_INICIAL_VARIACION,
    IMPRESIONES_BOLSA,
    MANIJAS_BOLSA,
)


def _crear_variaciones_de_bolsa(
    formato: FormatoBolsa,
    color: str,
    color_inicial: str,
    var_id_inicial: int,
) -> tuple[list[VariacionProducto], int]:
    """Crea las 6 variaciones de una bolsa según manija e impresión."""
    variaciones: list[VariacionProducto] = []
    var_id = var_id_inicial

    for manija, manija_inicial in MANIJAS_BOLSA:
        for impresion, impresion_inicial in IMPRESIONES_BOLSA:
            sku = construir_sku_bolsa(
                formato.codigo,
                color_inicial,
                manija_inicial,
                impresion_inicial,
            )
            variacion = VariacionProducto(
                id=var_id,
                sku=sku,
                atributos={"manija": manija, "impresion": impresion},
                imagen=imagen_para_manija(manija),
                cantidad_por_defecto=moq_para_impresion(impresion),
                calculo=calculo_articulo_para_bolsa(manija, impresion),
                visible=False,
            )
            variaciones.append(variacion)
            var_id += 1

    return variaciones, var_id


def crear_bolsas_base() -> tuple[
    list[ProductoBien],
    dict[int, VariacionProducto],
    dict[int, tuple[ProductoBien, VariacionProducto]],
    int,
]:
    """Crea los bienes simples de bolsa y sus variaciones.

    Los bienes simples no son visibles; los formatos visibles se exponen como
    compuestos (bobina + confección).
    """
    productos: list[ProductoBien] = []
    variacion_base_por_producto: dict[int, VariacionProducto] = {}
    variaciones: dict[int, tuple[ProductoBien, VariacionProducto]] = {}

    prod_id = ID_INICIAL_PRODUCTO_BOLSA
    var_id = ID_INICIAL_VARIACION

    for formato in FORMATOS_BOLSA:
        for color, color_name, color_slug in COLORES_BOLSA:
            slug = f"bolsa-de-papel-{color_slug}-{formato.codigo}"
            if formato.codigo == "221030" and color == "Marrón":
                slug = f"{slug}-base"

            nombre = f"Bolsa de Papel {color_name} {formato.rubro} ({formato.medidas})"
            descripcion = (
                f"Bolsa de papel de color {color.lower()} y formato {formato.medidas} "
                f"(Modelo {formato.codigo}). Diseñada especialmente {formato.rubro}. "
                "Ideal para comercios y despachos."
            )

            variaciones_bolsa, var_id = _crear_variaciones_de_bolsa(
                formato, color, "M" if color == "Marrón" else "B", var_id
            )

            producto = ProductoBien(
                tipo="bien",
                id=prod_id,
                nombre=nombre,
                descripcion=descripcion,
                slug=slug,
                imagen="bolsas-sin-m.svg",
                atributos_posibles={
                    "manija": ["Sin Manija", "Manija Cordón"],
                    "impresion": [
                        "Lisa (sin impresión)",
                        "Impresa 1 o 2 colores",
                        "Impresa Cuatricromía",
                    ],
                },
                variaciones=variaciones_bolsa,
                componentes=[],
                visible=False,
            )

            for variacion in variaciones_bolsa:
                variaciones[variacion.id] = (producto, variacion)

            variacion_base_por_producto[prod_id] = variaciones_bolsa[0]
            productos.append(producto)
            prod_id += 1

    return productos, variacion_base_por_producto, variaciones, var_id
