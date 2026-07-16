"""Orquestador de la construcción del catálogo en memoria.

Este módulo ensambla las distintas familias de productos definidas en los
módulos `bolsas`, `componentes`, `servicios` y `compuestos`.
"""

from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import ProductoBien, ProductoServicio

from .bolsas import crear_bolsas_base
from .componentes import crear_bobina, crear_componentes
from .compuestos import (
    crear_compuestos_impresos_con_manija_por_formato,
    crear_compuestos_impresos_por_formato,
    crear_compuestos_manija_por_formato,
    crear_compuestos_predefinidos,
)
from .data import (
    ID_BASE_COMPUESTOS_CON_MANIJA,
    ID_BASE_COMPUESTOS_IMPRESOS,
    ID_BASE_COMPUESTOS_IMPRESOS_CON_MANIJA,
)
from .servicios import crear_servicios


def construir_catalogo() -> tuple[
    list[ProductoBien | ProductoServicio],
    dict[int, tuple[ProductoBien, VariacionProducto]],
    dict[int, ProductoServicio],
]:
    """Construye el catálogo completo en memoria.

    Devuelve:
        - Lista de productos en el orden esperado por los tests y la UI.
        - Diccionario de variaciones indexadas por ID.
        - Diccionario de servicios indexados por ID.
    """
    bolsas_base, variacion_base_por_producto, variaciones, siguiente_var_id = (
        crear_bolsas_base()
    )

    (
        _manija_plana,
        manija_cordon,
        fotopolimero,
        variaciones_componentes,
        siguiente_var_id,
    ) = crear_componentes(siguiente_var_id)

    bobina, variaciones_bobina, siguiente_var_id = crear_bobina(siguiente_var_id)

    variaciones.update(variaciones_componentes)
    variaciones.update(variaciones_bobina)

    pegado, impresion, confeccion, corte_bobinas, confeccion_cuerdas = crear_servicios()
    servicios = {s.id: s for s in [pegado, impresion, confeccion, corte_bobinas, confeccion_cuerdas]}

    variacion_bolsa_base = variaciones[1][1]

    compuestos_predefinidos = crear_compuestos_predefinidos(
        variacion_bolsa_base=variacion_bolsa_base,
        manija_cordon=manija_cordon,
        fotopolimero=fotopolimero,
        pegado=pegado,
        impresion=impresion,
        confeccion=confeccion,
        corte_bobinas=corte_bobinas,
        confeccion_cuerdas=confeccion_cuerdas,
        bobina=bobina,
    )

    compuestos_con_manija = crear_compuestos_manija_por_formato(
        bolsas_base=bolsas_base,
        variacion_base_por_producto=variacion_base_por_producto,
        manija_cordon=manija_cordon,
        pegado=pegado,
        id_inicial=ID_BASE_COMPUESTOS_CON_MANIJA,
    )

    compuestos_impresos = crear_compuestos_impresos_por_formato(
        bolsas_base=bolsas_base,
        variacion_base_por_producto=variacion_base_por_producto,
        fotopolimero=fotopolimero,
        impresion=impresion,
        id_inicial=ID_BASE_COMPUESTOS_IMPRESOS,
    )

    compuestos_impresos_con_manija = crear_compuestos_impresos_con_manija_por_formato(
        bolsas_base=bolsas_base,
        variacion_base_por_producto=variacion_base_por_producto,
        manija_cordon=manija_cordon,
        fotopolimero=fotopolimero,
        impresion=impresion,
        pegado=pegado,
        id_inicial=ID_BASE_COMPUESTOS_IMPRESOS_CON_MANIJA,
    )

    productos: list[ProductoBien | ProductoServicio] = [
        *bolsas_base,
        _manija_plana,
        manija_cordon,
        fotopolimero,
        bobina,
        pegado,
        impresion,
        confeccion,
        corte_bobinas,
        confeccion_cuerdas,
        *compuestos_predefinidos,
        *compuestos_con_manija,
        *compuestos_impresos,
        *compuestos_impresos_con_manija,
    ]

    return productos, variaciones, servicios
