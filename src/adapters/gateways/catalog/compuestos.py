"""Builders para bienes compuestos del catálogo."""

from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import ComponenteBien, MedidasBolsa, ProductoBien, ProductoServicio

from .data import (
    SLUG_BOLSA_VISIBLE_CON_MANIJA,
    SLUG_BOLSA_VISIBLE_IMPRESA_CON_MANIJA,
    SLUG_BOLSA_VISIBLE_IMPRESA_SIN_MANIJA,
)


def _slug_impreso_desde_bolsa_base(producto: ProductoBien, sufijo: str = "") -> str:
    """Construye el slug de un producto impreso a partir del slug de la bolsa base.

    Las bolsas base siempre tienen slug definido. Si no fuera así, falla
    explícitamente para evitar slugs inválidos.
    """
    if producto.slug is None:
        raise ValueError(f"La bolsa base {producto.id} no tiene slug definido")
    slug = producto.slug.replace("bolsa-de-papel-", "bolsa-de-papel-impresa-", 1)
    if sufijo:
        slug = f"{slug}-{sufijo}"
    return slug


def crear_compuestos_predefinidos(
    variacion_bolsa_base: VariacionProducto,
    manija_cordon: ProductoBien,
    fotopolimero: ProductoBien,
    pegado: ProductoServicio,
    impresion: ProductoServicio,
    confeccion: ProductoServicio,
    bobina: ProductoBien,
) -> list[ProductoBien]:
    """Crea los 4 compuestos fijos del catálogo."""
    bolsa_con_manija = ProductoBien(
        tipo="bien",
        id=3001,
        nombre="Bolsa de Papel con Manija Cordón",
        descripcion="Bolsa de papel con manija cordón ya pegada. Receta fija lista para usar.",
        slug="bolsa-de-papel-con-manija-cordon",
        imagen="bolsas-con-m.svg",
        cantidad_por_defecto=1000,
        atributos_posibles={},
        variaciones=[],
        visible=False,
        componentes=[
            ComponenteBien(
                tipo="variacion",
                referencia_id=variacion_bolsa_base.id,
                cantidad=1,
                nombre="Bolsa de papel base",
            ),
            ComponenteBien(
                tipo="variacion",
                referencia_id=manija_cordon.variaciones[0].id,
                cantidad=1,
                nombre=manija_cordon.nombre,
            ),
            ComponenteBien(
                tipo="servicio",
                referencia_id=pegado.id,
                cantidad=1,
                nombre=pegado.nombre,
            ),
        ],
    )

    bolsa_impresa = ProductoBien(
        tipo="bien",
        id=3002,
        nombre="Bolsa de Papel Impresa",
        descripcion="Bolsa de papel impresa en 1 o 2 colores. Receta fija lista para cotizar.",
        slug="bolsa-de-papel-impresa",
        imagen="bolsas-personalizadas.svg",
        cantidad_por_defecto=1000,
        atributos_posibles={},
        variaciones=[],
        componentes=[
            ComponenteBien(
                tipo="variacion",
                referencia_id=variacion_bolsa_base.id,
                cantidad=1,
                nombre="Bolsa de papel base",
            ),
            ComponenteBien(
                tipo="servicio",
                referencia_id=impresion.id,
                cantidad=1,
                nombre=impresion.nombre,
            ),
        ],
    )

    bolsa_impresa_foto = ProductoBien(
        tipo="bien",
        id=3003,
        nombre="Bolsa de Papel Impresa con Fotopolímero",
        descripcion="Bolsa de papel impresa incluyendo fotopolímero para la matriz de impresión.",
        slug="bolsa-de-papel-impresa-con-fotopolimero",
        imagen="bolsas-personalizadas.svg",
        cantidad_por_defecto=1000,
        atributos_posibles={},
        variaciones=[],
        componentes=[
            ComponenteBien(
                tipo="variacion",
                referencia_id=variacion_bolsa_base.id,
                cantidad=1,
                nombre="Bolsa de papel base",
            ),
            ComponenteBien(
                tipo="servicio",
                referencia_id=impresion.id,
                cantidad=1,
                nombre=impresion.nombre,
            ),
            ComponenteBien(
                tipo="variacion",
                referencia_id=fotopolimero.variaciones[0].id,
                cantidad=1,
                nombre=fotopolimero.nombre,
            ),
        ],
    )

    bolsa_de_papel = ProductoBien(
        tipo="bien",
        id=3004,
        nombre="Bolsa de Papel Kraft Marrón para Hamburguesas y Delivery (22x10x30 cm)",
        descripcion="Bolsa de papel resultado de bobina de papel kraft + servicio de confección.",
        slug="bolsa-de-papel-marron-221030",
        imagen="bolsas-sin-m.svg",
        cantidad_por_defecto=1000,
        atributos_posibles={},
        variaciones=[],
        visible=True,
        componentes=[
            ComponenteBien(
                tipo="variacion",
                referencia_id=bobina.variaciones[0].id,
                cantidad=1,
                nombre=bobina.nombre,
                medidas=MedidasBolsa(ancho=22, fuelle=10, alto=30),
                gramaje=100,
            ),
            ComponenteBien(
                tipo="servicio",
                referencia_id=confeccion.id,
                cantidad=1,
                nombre=confeccion.nombre,
            ),
        ],
    )

    return [bolsa_con_manija, bolsa_impresa, bolsa_impresa_foto, bolsa_de_papel]


def crear_compuestos_impresos_por_formato(
    bolsas_base: list[ProductoBien],
    variacion_base_por_producto: dict[int, VariacionProducto],
    fotopolimero: ProductoBien,
    impresion: ProductoServicio,
    id_inicial: int,
) -> list[ProductoBien]:
    """Crea compuestos impresos (con/sin fotopolímero) para cada bolsa simple base."""
    compuestos: list[ProductoBien] = []
    compuesto_id = id_inicial

    for producto in bolsas_base:
        variacion_base = variacion_base_por_producto[producto.id]
        nombre_base = producto.nombre

        # Impreso sin fotopolímero
        slug = _slug_impreso_desde_bolsa_base(producto)
        nombre = f"Bolsa de Papel Impresa 1 o 2 colores {nombre_base}"
        compuestos.append(
            ProductoBien(
                tipo="bien",
                id=compuesto_id,
                nombre=nombre,
                descripcion=f"{nombre_base} impresa en 1 o 2 colores. Receta fija lista para cotizar.",
                slug=slug,
                imagen="bolsas-personalizadas.svg",
                cantidad_por_defecto=1000,
                atributos_posibles={},
                variaciones=[],
                visible=slug == SLUG_BOLSA_VISIBLE_IMPRESA_SIN_MANIJA,
                componentes=[
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=variacion_base.id,
                        cantidad=1,
                        nombre="Bolsa de papel base",
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=impresion.id,
                        cantidad=1,
                        nombre=impresion.nombre,
                    ),
                ],
            )
        )
        compuesto_id += 1

        # Impreso con fotopolímero
        slug = _slug_impreso_desde_bolsa_base(producto, "con-fotopolimero")
        nombre = f"Bolsa de Papel Impresa 1 o 2 colores con Fotopolímero {nombre_base}"
        compuestos.append(
            ProductoBien(
                tipo="bien",
                id=compuesto_id,
                nombre=nombre,
                descripcion=f"{nombre_base} impresa en 1 o 2 colores incluyendo fotopolímero para la matriz de impresión.",
                slug=slug,
                imagen="bolsas-personalizadas.svg",
                cantidad_por_defecto=1000,
                atributos_posibles={},
                variaciones=[],
                visible=False,
                componentes=[
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=variacion_base.id,
                        cantidad=1,
                        nombre="Bolsa de papel base",
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=impresion.id,
                        cantidad=1,
                        nombre=impresion.nombre,
                    ),
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=fotopolimero.variaciones[0].id,
                        cantidad=1,
                        nombre=fotopolimero.nombre,
                    ),
                ],
            )
        )
        compuesto_id += 1

    return compuestos


def crear_compuestos_impresos_con_manija_por_formato(
    bolsas_base: list[ProductoBien],
    variacion_base_por_producto: dict[int, VariacionProducto],
    manija_cordon: ProductoBien,
    fotopolimero: ProductoBien,
    impresion: ProductoServicio,
    pegado: ProductoServicio,
    id_inicial: int,
) -> list[ProductoBien]:
    """Crea compuestos impresos con manija cordón (con/sin fotopolímero) por formato."""
    compuestos: list[ProductoBien] = []
    compuesto_id = id_inicial

    for producto in bolsas_base:
        variacion_base = variacion_base_por_producto[producto.id]
        nombre_base = producto.nombre

        # Impreso con manija cordón, sin fotopolímero
        slug = _slug_impreso_desde_bolsa_base(producto, "con-manija-cordon")
        nombre = f"Bolsa de Papel Impresa 1 o 2 colores con Manija Cordón {nombre_base}"
        compuestos.append(
            ProductoBien(
                tipo="bien",
                id=compuesto_id,
                nombre=nombre,
                descripcion=f"{nombre_base} impresa en 1 o 2 colores con manija cordón ya pegada. Receta fija lista para cotizar.",
                slug=slug,
                imagen="bolsas-con-m.svg",
                cantidad_por_defecto=variacion_base.cantidad_por_defecto,
                atributos_posibles={},
                variaciones=[],
                visible=slug == SLUG_BOLSA_VISIBLE_IMPRESA_CON_MANIJA,
                componentes=[
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=variacion_base.id,
                        cantidad=1,
                        nombre="Bolsa de papel base",
                    ),
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=manija_cordon.variaciones[0].id,
                        cantidad=1,
                        nombre=manija_cordon.nombre,
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=pegado.id,
                        cantidad=1,
                        nombre=pegado.nombre,
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=impresion.id,
                        cantidad=1,
                        nombre=impresion.nombre,
                    ),
                ],
            )
        )
        compuesto_id += 1

        # Impreso con manija cordón y fotopolímero
        slug = _slug_impreso_desde_bolsa_base(producto, "con-manija-cordon-y-fotopolimero")
        nombre = f"Bolsa de Papel Impresa 1 o 2 colores con Manija Cordón y Fotopolímero {nombre_base}"
        compuestos.append(
            ProductoBien(
                tipo="bien",
                id=compuesto_id,
                nombre=nombre,
                descripcion=f"{nombre_base} impresa en 1 o 2 colores con manija cordón ya pegada e incluyendo fotopolímero.",
                slug=slug,
                imagen="bolsas-con-m.svg",
                cantidad_por_defecto=variacion_base.cantidad_por_defecto,
                atributos_posibles={},
                variaciones=[],
                visible=False,
                componentes=[
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=variacion_base.id,
                        cantidad=1,
                        nombre="Bolsa de papel base",
                    ),
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=manija_cordon.variaciones[0].id,
                        cantidad=1,
                        nombre=manija_cordon.nombre,
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=pegado.id,
                        cantidad=1,
                        nombre=pegado.nombre,
                    ),
                    ComponenteBien(
                        tipo="servicio",
                        referencia_id=impresion.id,
                        cantidad=1,
                        nombre=impresion.nombre,
                    ),
                    ComponenteBien(
                        tipo="variacion",
                        referencia_id=fotopolimero.variaciones[0].id,
                        cantidad=1,
                        nombre=fotopolimero.nombre,
                    ),
                ],
            )
        )
        compuesto_id += 1

    return compuestos


def crear_compuestos_manija_por_formato(
    bolsas_base: list[ProductoBien],
    variacion_base_por_producto: dict[int, VariacionProducto],
    manija_cordon: ProductoBien,
    pegado: ProductoServicio,
    id_inicial: int,
) -> list[ProductoBien]:
    """Crea un compuesto "con manija cordón" para cada bolsa simple base."""
    compuestos: list[ProductoBien] = []
    compuesto_id = id_inicial

    for producto in bolsas_base:
        variacion_base = variacion_base_por_producto[producto.id]
        nombre_compuesto = f"{producto.nombre} con Manija Cordón"
        slug_compuesto = f"{producto.slug}-con-manija-cordon"

        compuesto = ProductoBien(
            tipo="bien",
            id=compuesto_id,
            nombre=nombre_compuesto,
            descripcion=f"{producto.nombre} con manija cordón ya pegada. Receta fija lista para usar.",
            slug=slug_compuesto,
            imagen="bolsas-con-m.svg",
            cantidad_por_defecto=variacion_base.cantidad_por_defecto,
            atributos_posibles={},
            variaciones=[],
            visible=producto.slug == SLUG_BOLSA_VISIBLE_CON_MANIJA,
            componentes=[
                ComponenteBien(
                    tipo="variacion",
                    referencia_id=variacion_base.id,
                    cantidad=1,
                    nombre="Bolsa de papel base",
                ),
                ComponenteBien(
                    tipo="variacion",
                    referencia_id=manija_cordon.variaciones[0].id,
                    cantidad=1,
                    nombre=manija_cordon.nombre,
                ),
                ComponenteBien(
                    tipo="servicio",
                    referencia_id=pegado.id,
                    cantidad=1,
                    nombre=pegado.nombre,
                ),
            ],
        )
        compuestos.append(compuesto)
        compuesto_id += 1

    return compuestos
