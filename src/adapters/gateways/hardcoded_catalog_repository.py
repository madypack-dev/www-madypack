from src.domain.commerce.cart import CalculoArticulo
from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import ComponenteBien, MedidasBolsa, ProductoBien, ProductoServicio


class HardcodedCatalogRepository(ICatalogRepository):
    """Implementación de ICatalogRepository con bienes (simples/compuestos) y servicios.

    Los identificadores se reparten en rangos disjuntos para evitar colisiones con
    las líneas de carrito:
        - Variaciones: 1..N
        - Bienes: 1001..
        - Servicios: 2001..
    """

    def __init__(self) -> None:
        self._productos: list[ProductoBien | ProductoServicio] = []
        self._variaciones: dict[int, tuple[ProductoBien, VariacionProducto]] = {}
        self._servicios: dict[int, ProductoServicio] = {}

        self._generar_bienes_bolsas()
        manija_plana, manija_cordon, fotopolimero = self._generar_bienes_componentes()
        bobina = self._generar_bobina()
        pegado, impresion, confeccion = self._generar_servicios()
        self._generar_bienes_compuestos(
            manija_cordon=manija_cordon,
            fotopolimero=fotopolimero,
            pegado=pegado,
            impresion=impresion,
            confeccion=confeccion,
            bobina=bobina,
        )

    def _generar_bienes_bolsas(self) -> None:
        formatos = [
            {"codigo": "120819", "medidas": "12x8x19 cm", "rubro": "para Farmacia y Joyería"},
            {"codigo": "120841", "medidas": "12x8x41 cm", "rubro": "para Vinos y Licores"},
            {"codigo": "161024", "medidas": "16x10x24 cm", "rubro": "para Delivery Chico y Cafetería"},
            {"codigo": "221030", "medidas": "22x10x30 cm", "rubro": "para Hamburguesas y Delivery"},
            {"codigo": "261236", "medidas": "26x12x36 cm", "rubro": "para Indumentaria y Tiendas"},
            {"codigo": "301241", "medidas": "30x12x41 cm", "rubro": "para Calzado y Abrigos"},
        ]

        prod_id = 1001
        var_id = 1

        for f in formatos:
            for color in ["Marrón", "Blanco"]:
                color_name = "Kraft Marrón" if color == "Marrón" else "Blanca"
                color_slug = "marron" if color == "Marrón" else "blanco"
                # Los bienes simples de bolsa no son visibles; los formatos visibles
                # se exponen como compuestos (bobina + confección).
                es_visible_simple = False
                slug = f"bolsa-de-papel-{color_slug}-{f['codigo']}"
                if f["codigo"] == "221030" and color == "Marrón":
                    slug = f"{slug}-base"
                nombre_prod = f"Bolsa de Papel {color_name} {f['rubro']} ({f['medidas']})"
                desc = (
                    f"Bolsa de papel de color {color.lower()} y formato {f['medidas']} "
                    f"(Modelo {f['codigo']}). Diseñada especialmente {f['rubro']}. "
                    "Ideal para comercios y despachos."
                )

                variaciones: list[VariacionProducto] = []
                for manija in ["Sin Manija", "Manija Cordón"]:
                    for impresion in [
                        "Lisa (sin impresión)",
                        "Impresa 1 o 2 colores",
                        "Impresa Cuatricromía",
                    ]:
                        m_initial = "SOS" if manija == "Sin Manija" else "CRD"
                        c_initial = "M" if color == "Marrón" else "B"
                        i_initial = (
                            "L"
                            if "Lisa" in impresion
                            else ("I" if "1 o 2" in impresion else "C")
                        )
                        sku = f"B-{f['codigo']}-{c_initial}-{m_initial}-{i_initial}"
                        imagen = "bolsas-sin-m.svg" if manija == "Sin Manija" else "bolsas-con-m.svg"
                        moq = (
                            500
                            if "Lisa" in impresion
                            else (1000 if "1 o 2" in impresion else 3000)
                        )

                        variacion_visible = False

                        calculo = self._calculo_bolsa(manija, impresion)

                        variacion = VariacionProducto(
                            id=var_id,
                            sku=sku,
                            atributos={"manija": manija, "impresion": impresion},
                            imagen=imagen,
                            cantidad_por_defecto=moq,
                            calculo=calculo,
                            visible=variacion_visible,
                        )
                        variaciones.append(variacion)
                        var_id += 1

                producto = ProductoBien(
                    tipo="bien",
                    id=prod_id,
                    nombre=nombre_prod,
                    descripcion=desc,
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
                    variaciones=variaciones,
                    componentes=[],
                    visible=es_visible_simple,
                )

                for variacion in variaciones:
                    self._variaciones[variacion.id] = (producto, variacion)

                self._productos.append(producto)
                prod_id += 1

    def _calculo_bolsa(self, manija: str, impresion: str) -> CalculoArticulo:
        conceptos = ["base"]
        concepto_fijo = None

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

    def _generar_bienes_componentes(
        self,
    ) -> tuple[ProductoBien, ProductoBien, ProductoBien]:
        var_id = 73

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
        self._variaciones[var_id] = (manija_plana, manija_plana.variaciones[0])
        var_id += 1

        manija_cordon = ProductoBien(
            tipo="bien",
            id=1102,
            nombre="Manija Cordón",
            descripcion="Manija cordón de papel kraft para pegado manual o automático.",
            slug="manija-cordon",
            imagen="bolsas-con-m.svg",
            atributos_posibles={"tipo": ["Cordón"]},
            variaciones=[
                VariacionProducto(
                    id=var_id,
                    sku="MAN-C",
                    atributos={"tipo": "Cordón"},
                    imagen="bolsas-con-m.svg",
                    cantidad_por_defecto=1000,
                    calculo=CalculoArticulo(
                        tipo="suma_por_unidad", conceptos=["manija_cordon"]
                    ),
                )
            ],
            componentes=[],
        )
        self._variaciones[var_id] = (manija_cordon, manija_cordon.variaciones[0])
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
        self._variaciones[var_id] = (fotopolimero, fotopolimero.variaciones[0])

        self._productos.extend([manija_plana, manija_cordon, fotopolimero])
        return manija_plana, manija_cordon, fotopolimero

    def _generar_bobina(self) -> ProductoBien:
        var_id = 76
        bobina = ProductoBien(
            tipo="bien",
            id=1104,
            nombre="Bobina de Papel",
            descripcion="Materia prima: bobina de papel kraft para confección de bolsas.",
            slug="bobina-de-papel",
            imagen="bobina-de-papel.svg",
            atributos_posibles={"tipo": ["Kraft Marrón"]},
            variaciones=[
                VariacionProducto(
                    id=var_id,
                    sku="BOB-001",
                    atributos={"tipo": "Kraft Marrón"},
                    imagen="bobina-de-papel.svg",
                    cantidad_por_defecto=1000,
                    calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["base"]),
                    visible=True,
                )
            ],
            componentes=[],
            visible=True,
        )
        self._variaciones[var_id] = (bobina, bobina.variaciones[0])
        self._productos.append(bobina)
        return bobina

    def _generar_servicios(self) -> tuple[ProductoServicio, ProductoServicio, ProductoServicio]:
        pegado = ProductoServicio(
            tipo="servicio",
            id=2001,
            nombre="Pegado de Manijas",
            descripcion="Servicio de pegado de manijas sobre bolsas de papel.",
            slug="pegado-de-manijas",
            imagen="icon-hand.svg",
            calculo=CalculoArticulo(tipo="suma_por_unidad", conceptos=["pegado"]),
            cantidad_por_defecto=1000,
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

        self._servicios[pegado.id] = pegado
        self._servicios[impresion.id] = impresion
        self._servicios[confeccion.id] = confeccion
        self._productos.extend([pegado, impresion, confeccion])
        return pegado, impresion, confeccion

    def _generar_bienes_compuestos(
        self,
        manija_cordon: ProductoBien,
        fotopolimero: ProductoBien,
        pegado: ProductoServicio,
        impresion: ProductoServicio,
        confeccion: ProductoServicio,
        bobina: ProductoBien,
    ) -> None:
        # Variación de bolsa base: 12x8x19 cm, Marrón, Sin Manija, Lisa
        bolsa_base = self._variaciones.get(1)
        if not bolsa_base:
            return

        _, variacion_bolsa_base = bolsa_base

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

        # "Bolsas de papel" 22x10x30 como bobina + confección (producto visible)
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

        self._productos.extend([bolsa_con_manija, bolsa_impresa, bolsa_impresa_foto, bolsa_de_papel])

    def obtener_todos(self) -> list[ProductoBien | ProductoServicio]:
        return self._productos

    def obtener_por_id(self, id_producto: int) -> ProductoBien | ProductoServicio | None:
        return next((p for p in self._productos if p.id == id_producto), None)

    def obtener_por_slug(self, slug: str) -> ProductoBien | ProductoServicio | None:
        return next((p for p in self._productos if p.url_slug == slug), None)

    def buscar(self, query: str) -> list[ProductoBien | ProductoServicio]:
        query_filtrada = query.strip().lower()
        if not query_filtrada:
            return self._productos
        return [
            p
            for p in self._productos
            if query_filtrada in p.nombre.lower()
            or query_filtrada in p.descripcion.lower()
        ]

    def obtener_variacion_por_id(
        self, id_variacion: int
    ) -> tuple[ProductoBien, VariacionProducto] | None:
        return self._variaciones.get(id_variacion)

    def obtener_servicio_por_id(self, id_servicio: int) -> ProductoServicio | None:
        return self._servicios.get(id_servicio)

    def resolver_componente(
        self, componente: ComponenteBien
    ) -> VariacionProducto | ProductoServicio | None:
        if componente.tipo == "variacion":
            res = self._variaciones.get(componente.referencia_id)
            if res:
                return res[1]
            return None
        if componente.tipo == "servicio":
            return self._servicios.get(componente.referencia_id)
        return None
