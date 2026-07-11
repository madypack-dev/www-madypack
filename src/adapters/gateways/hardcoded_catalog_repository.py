from src.domain.commerce.catalog import ProductoVariable, VariacionProducto
from src.domain.commerce.catalog_repository import ICatalogRepository


class HardcodedCatalogRepository(ICatalogRepository):
    """Implementación de ICatalogRepository con 12 productos variables y 72 variaciones generadas programáticamente."""

    def __init__(self) -> None:
        # Formatos reales extraídos del Tablero de Madygraf
        formatos = [
            {"codigo": "120819", "medidas": "12x8x19 cm", "nombre": "Chica SOS"},
            {"codigo": "120841", "medidas": "12x8x41 cm", "nombre": "Fondo Americano Alto"},
            {"codigo": "161024", "medidas": "16x10x24 cm", "nombre": "Mediana SOS"},
            {"codigo": "221030", "medidas": "22x10x30 cm", "nombre": "Estándar Chica"},
            {"codigo": "261236", "medidas": "26x12x36 cm", "nombre": "Estándar Mediana"},
            {"codigo": "301241", "medidas": "30x12x41 cm", "nombre": "Estándar Grande"},
        ]

        self._productos = []
        prod_id = 1
        var_id = 1

        for f in formatos:
            for color in ["Marrón", "Blanco"]:
                nombre_prod = f"Bolsa de Papel {color} - {f['nombre']} ({f['medidas']})"
                color_slug = "marron" if color == "Marrón" else "blanco"
                slug = f"bolsa-de-papel-{color_slug}-{f['codigo']}"
                desc = f"Bolsa de papel de color {color.lower()} y formato {f['medidas']} (Modelo {f['codigo']}). Ideal para todo tipo de comercios, despachos y delivery."

                # Generar las 6 variaciones (Manija x Impresión) para este producto
                variaciones = []
                for manija in ["Sin Manija", "Manija Cordón"]:
                    for impresion in [
                        "Lisa (sin impresión)",
                        "Impresa 1 o 2 colores",
                        "Impresa Cuatricromía",
                    ]:
                        # Formato de SKU: B - MODELO - COLOR - MANIJA - IMPRESION
                        m_initial = "SOS" if manija == "Sin Manija" else "CRD"
                        c_initial = "M" if color == "Marrón" else "B"
                        i_initial = (
                            "L"
                            if "Lisa" in impresion
                            else ("I" if "1 o 2" in impresion else "C")
                        )
                        sku = f"B-{f['codigo']}-{c_initial}-{m_initial}-{i_initial}"

                        imagen = (
                            "bolsas-sin-m.svg"
                            if manija == "Sin Manija"
                            else "bolsas-con-m.svg"
                        )

                        # Cantidad mínima sugerida (MOQ) según impresión
                        moq = (
                            500
                            if "Lisa" in impresion
                            else (1000 if "1 o 2" in impresion else 3000)
                        )

                        variaciones.append(
                            VariacionProducto(
                                id=var_id,
                                sku=sku,
                                atributos={
                                    "manija": manija,
                                    "impresion": impresion,
                                },
                                imagen=imagen,
                                cantidad_por_defecto=moq,
                                calculo=None,
                            )
                        )
                        var_id += 1

                self._productos.append(
                    ProductoVariable(
                        id=prod_id,
                        nombre=nombre_prod,
                        descripcion=desc,
                        slug=slug,
                        atributos_posibles={
                            "manija": ["Sin Manija", "Manija Cordón"],
                            "impresion": [
                                "Lisa (sin impresión)",
                                "Impresa 1 o 2 colores",
                                "Impresa Cuatricromía",
                            ],
                        },
                        variaciones=variaciones,
                    )
                )
                prod_id += 1

    def obtener_todos(self) -> list[ProductoVariable]:
        return self._productos

    def obtener_por_id(self, id_producto: int) -> ProductoVariable | None:
        return next((p for p in self._productos if p.id == id_producto), None)

    def obtener_por_slug(self, slug: str) -> ProductoVariable | None:
        return next((p for p in self._productos if p.url_slug == slug), None)

    def buscar(self, query: str) -> list[ProductoVariable]:
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
    ) -> tuple[ProductoVariable, VariacionProducto] | None:
        for p in self._productos:
            for v in p.variaciones:
                if v.id == id_variacion:
                    return p, v
        return None
