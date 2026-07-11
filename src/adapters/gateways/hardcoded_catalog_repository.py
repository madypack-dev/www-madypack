from src.domain.commerce.catalog import ProductoVariable, VariacionProducto
from src.domain.commerce.catalog_repository import ICatalogRepository


class HardcodedCatalogRepository(ICatalogRepository):
    """Implementación de ICatalogRepository con productos variables y variaciones hardcodeadas en Python."""

    def __init__(self) -> None:
        self._productos = [
            ProductoVariable(
                id=1,
                nombre="Bolsa de Papel",
                descripcion="Bolsas de papel Kraft biodegradables para comercios, delivery, panadería y tiendas. Elegí la opción con o sin manijas y personalizala con tu marca.",
                slug="bolsa-de-papel",
                atributos_posibles={
                    "color": ["Marrón", "Blanco"],
                    "manija": ["Sin Manija", "Manija Cordón"],
                },
                variaciones=[
                    VariacionProducto(
                        id=1,
                        sku="B-SOS-M",
                        atributos={"color": "Marrón", "manija": "Sin Manija"},
                        imagen="bolsas-sin-m.svg",
                        cantidad_por_defecto=1000,
                        calculo=None,
                    ),
                    VariacionProducto(
                        id=2,
                        sku="B-SOS-B",
                        atributos={"color": "Blanco", "manija": "Sin Manija"},
                        imagen="bolsas-sin-m.svg",
                        cantidad_por_defecto=1000,
                        calculo=None,
                    ),
                    VariacionProducto(
                        id=3,
                        sku="B-CRD-M",
                        atributos={"color": "Marrón", "manija": "Manija Cordón"},
                        imagen="bolsas-con-m.svg",
                        cantidad_por_defecto=1000,
                        calculo=None,
                    ),
                    VariacionProducto(
                        id=4,
                        sku="B-CRD-B",
                        atributos={"color": "Blanco", "manija": "Manija Cordón"},
                        imagen="bolsas-con-m.svg",
                        cantidad_por_defecto=1000,
                        calculo=None,
                    ),
                ],
            )
        ]

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
