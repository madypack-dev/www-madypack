"""Builders para componentes adicionales: manijas, fotopolímero y bobina."""

from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import ProductoBien


def crear_componentes(
    var_id_inicial: int,
) -> tuple[
    ProductoBien,
    ProductoBien,
    ProductoBien,
    dict[int, tuple[ProductoBien, VariacionProducto]],
    int,
]:
    """Crea los componentes reutilizables: manija plana, cordón y fotopolímero."""
    variaciones: dict[int, tuple[ProductoBien, VariacionProducto]] = {}
    var_id = var_id_inicial

    manija_plana = ProductoBien(
        tipo="bien",
        id=1101,
        nombre="Manija Plana",
        descripcion="Manija plana de papel kraft para pegado manual o automático.",
        slug="manija-plana",
        imagen="bolsas-con-m.svg",
        atributos_posibles={"tipo": ["Plana"]},
        variaciones=[
            VariacionProducto(
                id=var_id,
                sku="MAN-P",
                atributos={"tipo": "Plana"},
                imagen="bolsas-con-m.svg",
                cantidad_por_defecto=1000,
                calculo=CalculoArticulo(
                    tipo="suma_por_unidad", conceptos=["manija_plana"]
                ),
            )
        ],
        componentes=[],
    )
    variaciones[var_id] = (manija_plana, manija_plana.variaciones[0])
    var_id += 1

    manija_cordon = ProductoBien(
        tipo="bien",
        id=1102,
        nombre="Manija Cordón",
        descripcion="Manija cordón de papel kraft para pegado manual o automático.",
        slug="manija-cordon",
        imagen="manija-cordon.svg",
        atributos_posibles={"tipo": ["Cordón"]},
        variaciones=[
            VariacionProducto(
                id=var_id,
                sku="MAN-C",
                atributos={"tipo": "Cordón"},
                imagen="manija-cordon.svg",
                cantidad_por_defecto=1000,
                calculo=CalculoArticulo(
                    tipo="suma_por_unidad", conceptos=["manija_cordon"]
                ),
                visible=True,
            )
        ],
        componentes=[],
        visible=True,
    )
    variaciones[var_id] = (manija_cordon, manija_cordon.variaciones[0])
    var_id += 1

    fotopolimero = ProductoBien(
        tipo="bien",
        id=1103,
        nombre="Fotopolímero",
        descripcion="Placa fotopolímera para impresión flexográfica en bolsas de papel.",
        slug="fotopolimero",
        imagen="bolsas-personalizadas.svg",
        atributos_posibles={"tipo": ["Estándar"]},
        variaciones=[
            VariacionProducto(
                id=var_id,
                sku="FOTO",
                atributos={"tipo": "Estándar"},
                imagen="bolsas-personalizadas.svg",
                cantidad_por_defecto=100,
                calculo=CalculoArticulo(
                    tipo="suma_por_unidad_mas_fijo",
                    conceptos=[],
                    concepto_fijo="fijo_matriz",
                ),
            )
        ],
        componentes=[],
    )
    variaciones[var_id] = (fotopolimero, fotopolimero.variaciones[0])

    return manija_plana, manija_cordon, fotopolimero, variaciones, var_id + 1


def crear_bobina(
    var_id_inicial: int,
) -> tuple[ProductoBien, dict[int, tuple[ProductoBien, VariacionProducto]], int]:
    """Crea el bien bobina de papel."""
    variacion = VariacionProducto(
        id=var_id_inicial,
        sku="BOB-001",
        atributos={"tipo": "Kraft Marrón"},
        imagen="bobina-de-papel.svg",
        cantidad_por_defecto=100,
        calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["bobina_kg"]),
        visible=True,
    )
    bobina = ProductoBien(
        tipo="bien",
        id=1104,
        nombre="Bobina de Papel",
        descripcion="Materia prima: bobina de papel kraft para confección de bolsas.",
        slug="bobina-de-papel",
        imagen="bobina-de-papel.svg",
        atributos_posibles={"tipo": ["Kraft Marrón"]},
        variaciones=[variacion],
        componentes=[],
        visible=True,
        unidad="kg",
    )
    variaciones = {var_id_inicial: (bobina, variacion)}
    return bobina, variaciones, var_id_inicial + 1
