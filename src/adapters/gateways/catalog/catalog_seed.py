from dataclasses import dataclass
from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import (
    ComponenteBien,
    MedidasBolsa,
    ProductoBien,
    ProductoServicio,
)


@dataclass(frozen=True)
class FormatoBolsa:
    codigo: str
    medidas: str
    rubro: str


_FORMATOS_BOLSA: list[FormatoBolsa] = [
    FormatoBolsa("120819", "12x8x19 cm", "para Farmacia y Joyería"),
    FormatoBolsa("120841", "12x8x41 cm", "para Vinos y Licores"),
    FormatoBolsa("161024", "16x10x24 cm", "para Delivery Chico y Cafetería"),
    FormatoBolsa("221030", "22x10x30 cm", "para Hamburguesas y Delivery"),
    FormatoBolsa("261236", "26x12x36 cm", "para Indumentaria y Tiendas"),
    FormatoBolsa("301241", "30x12x41 cm", "para Calzado y Abrigos"),
]

_COLORES_BOLSA: list[tuple[str, str, str]] = [
    ("Marrón", "Kraft Marrón", "marron"),
    ("Blanco", "Blanca", "blanco"),
]

_MANIJAS_BOLSA: list[tuple[str, str]] = [
    ("Sin Manija", "SOS"),
    ("Manija Cordón", "CRD"),
]

_IMPRESIONES_BOLSA: list[tuple[str, str]] = [
    ("Lisa (sin impresión)", "L"),
    ("Impresa 1 o 2 colores", "I"),
    ("Impresa Cuatricromía", "C"),
]

ID_INICIAL_PRODUCTO_BOLSA = 1001
ID_INICIAL_VARIACION = 1
ID_INICIAL_COMPONENTE = 1101
ID_INICIAL_SERVICIO = 2001
ID_INICIAL_COMPUESTO = 3001

def _construir_sku_bolsa(
    codigo: str,
    color_inicial: str,
    manija_inicial: str,
    impresion_inicial: str,
) -> str:
    return f"B-{codigo}-{color_inicial}-{manija_inicial}-{impresion_inicial}"

def _crear_calculo_para_bolsa(
    manija: str,
    impresion: str,
) -> CalculoArticulo:
    conceptos = ["base"]
    concepto_fijo: str | None = None

    if manija == "Manija Cordón":
        conceptos.append("manija_cordon")
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


def _cantidad_por_defecto_para_impresion(impresion: str) -> int:
    if "Lisa" in impresion:
        return 500
    if "1 o 2" in impresion:
        return 1000
    return 3000

def _imagen_para_manija(manija: str) -> str:
    return "bolsas-sin-m.svg" if manija == "Sin Manija" else "bolsas-con-m.svg"

def _crear_variaciones_de_bolsa(
    formato: FormatoBolsa,
    color: str,
    color_inicial: str,
    var_id_inicial: int,
) -> tuple[list[VariacionProducto], int]:
    variaciones: list[VariacionProducto] = []
    var_id = var_id_inicial

    for manija, manija_inicial in _MANIJAS_BOLSA:
        for impresion, impresion_inicial in _IMPRESIONES_BOLSA:
            sku = _construir_sku_bolsa(
                formato.codigo,
                color_inicial,
                manija_inicial,
                impresion_inicial,
            )
            variacion = VariacionProducto(
                id=var_id,
                sku=sku,
                atributos={"manija": manija, "impresion": impresion},
                imagen=_imagen_para_manija(manija),
                cantidad_por_defecto=_cantidad_por_defecto_para_impresion(impresion),
                calculo=_crear_calculo_para_bolsa(manija, impresion),
                visible=False,
            )
            variaciones.append(variacion)
            var_id += 1

    return variaciones, var_id

def _crear_bolsas_base() -> tuple[
    list[ProductoBien],
    dict[int, VariacionProducto],
    dict[int, tuple[ProductoBien, VariacionProducto]],
    int,
]:
    productos: list[ProductoBien] = []
    variacion_base_por_producto: dict[int, VariacionProducto] = {}
    variaciones: dict[int, tuple[ProductoBien, VariacionProducto]] = {}

    prod_id = ID_INICIAL_PRODUCTO_BOLSA
    var_id = ID_INICIAL_VARIACION

    for formato in _FORMATOS_BOLSA:
        for color, color_name, color_slug in _COLORES_BOLSA:
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


def _crear_componentes(
    var_id_inicial: int,
) -> tuple[
    ProductoBien,
    ProductoBien,
    ProductoBien,
    dict[int, tuple[ProductoBien, VariacionProducto]],
    int,
]:
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


def _crear_bobina(
    var_id_inicial: int,
) -> tuple[ProductoBien, dict[int, tuple[ProductoBien, VariacionProducto]], int]:
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


def _crear_servicios() -> tuple[ProductoServicio, ProductoServicio, ProductoServicio]:
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
    return pegado, impresion, confeccion

def _crear_compuestos_fijos(
    variacion_bolsa_base: VariacionProducto,
    manija_cordon: ProductoBien,
    fotopolimero: ProductoBien,
    pegado: ProductoServicio,
    impresion: ProductoServicio,
    confeccion: ProductoServicio,
    bobina: ProductoBien,
) -> list[ProductoBien]:
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


def _crear_compuestos_con_manija(
    bolsas_base: list[ProductoBien],
    variacion_base_por_producto: dict[int, VariacionProducto],
    manija_cordon: ProductoBien,
    pegado: ProductoServicio,
    id_inicial: int,
) -> list[ProductoBien]:
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
            visible=producto.slug == "bolsa-de-papel-marron-221030-base",
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


def construir_catalogo() -> tuple[
    list[ProductoBien | ProductoServicio],
    dict[int, tuple[ProductoBien, VariacionProducto]],
    dict[int, ProductoServicio],
]:
    bolsas_base, variacion_base_por_producto, variaciones, siguiente_var_id = (
        _crear_bolsas_base()
    )

    (
        _manija_plana,
        manija_cordon,
        fotopolimero,
        variaciones_componentes,
        siguiente_var_id,
    ) = _crear_componentes(siguiente_var_id)

    bobina, variaciones_bobina, siguiente_var_id = _crear_bobina(siguiente_var_id)

    variaciones.update(variaciones_componentes)
    variaciones.update(variaciones_bobina)

    pegado, impresion, confeccion = _crear_servicios()
    servicios = {s.id: s for s in [pegado, impresion, confeccion]}

    variacion_bolsa_base = variaciones[1][1]

    compuestos_fijos = _crear_compuestos_fijos(
        variacion_bolsa_base=variacion_bolsa_base,
        manija_cordon=manija_cordon,
        fotopolimero=fotopolimero,
        pegado=pegado,
        impresion=impresion,
        confeccion=confeccion,
        bobina=bobina,
    )

    compuestos_con_manija = _crear_compuestos_con_manija(
        bolsas_base=bolsas_base,
        variacion_base_por_producto=variacion_base_por_producto,
        manija_cordon=manija_cordon,
        pegado=pegado,
        id_inicial=ID_INICIAL_COMPUESTO + len(compuestos_fijos),
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
        *compuestos_fijos,
        *compuestos_con_manija,
    ]

    return productos, variaciones, servicios
