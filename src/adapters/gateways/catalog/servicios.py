"""Builders para servicios del catálogo."""

from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.product import ProductoServicio


def crear_servicios() -> tuple[
    ProductoServicio,
    ProductoServicio,
    ProductoServicio,
    ProductoServicio,
    ProductoServicio,
]:
    """Crea los servicios del catálogo."""
    pegado = ProductoServicio(
        tipo="servicio",
        id=2001,
        nombre="Pegado de Manijas",
        descripcion="Servicio de pegado de manijas sobre bolsas de papel.",
        slug="pegado-de-manijas",
        imagen="icon-hand.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["pegado"]),
        cantidad_por_defecto=1000,
        visible=True,
    )
    impresion = ProductoServicio(
        tipo="servicio",
        id=2002,
        nombre="Impresión",
        descripcion="Servicio de impresión flexográfica en bolsas de papel.",
        slug="impresion",
        imagen="bolsas-personalizadas.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["personalizacion"]),
        cantidad_por_defecto=1000,
    )
    confeccion = ProductoServicio(
        tipo="servicio",
        id=2003,
        nombre="Confección de Bolsas de Papel",
        descripcion="Servicio de confección que transforma bobinas de papel en bolsas terminadas.",
        slug="confeccion-de-bolsas",
        imagen="icon-hoja.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["confeccion"]),
        cantidad_por_defecto=1000,
        visible=True,
    )
    corte_bobinas = ProductoServicio(
        tipo="servicio",
        id=2004,
        nombre="Corte de Bobinas",
        descripcion="Servicio de corte de bobinas de papel kraft.",
        slug="corte-de-bobinas",
        imagen="icon-hoja.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["corte"]),
        cantidad_por_defecto=1000,
        visible=True,
    )
    confeccion_cuerdas = ProductoServicio(
        tipo="servicio",
        id=2005,
        nombre="Confección de Cuerdas de Papel Retorcidas",
        descripcion="Servicio de confección de cuerdas de papel retorcidas a partir de bobinas.",
        slug="confeccion-de-cuerdas-de-papel-retorcidas",
        imagen="icon-hoja.svg",
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["confeccion_cuerdas"]),
        cantidad_por_defecto=1000,
        visible=True,
    )
    return pegado, impresion, confeccion, corte_bobinas, confeccion_cuerdas
