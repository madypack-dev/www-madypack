from src.domain.commerce.catalog import ArticuloCatalogo
from src.domain.commerce.catalog_repository import ICatalogRepository

class HardcodedCatalogRepository(ICatalogRepository):
    """Implementación de ICatalogRepository con productos hardcodeados directamente en Python."""

    def __init__(self) -> None:
        self._articulos = [
            ArticuloCatalogo(
                id=1,
                nombre="Bolsas de Papel Kraft Marrón sin Manija",
                descripcion="Gramaje: 80 gr/m² | Lisas o personalizadas a 1 o 2 colores. Ideal para delivery, panadería y almacén.",
                cantidad_por_defecto=1000,
                imagen="bolsas-sin-m.svg",
                slug="bolsas-kraft-marron-sin-manija"
            ),
            ArticuloCatalogo(
                id=2,
                nombre="Bolsas de Papel Blanco sin Manija",
                descripcion="Gramaje: 80 gr/m² | Lisas o personalizadas a 1 o 2 colores. Excelente presentación para farmacias, panificados y delivery.",
                cantidad_por_defecto=1000,
                imagen="bolsas-sin-m.svg",
                slug="bolsas-blancas-sin-manija"
            ),
            ArticuloCatalogo(
                id=3,
                nombre="Bolsas de Papel Kraft Marrón con Manija Cordón",
                descripcion="Gramaje: 100 gr/m² | Manija cordón retorcido de papel. Máxima resistencia. Lisas, personalizadas (1 o 2 colores) o cuatricromía (para grandes cantidades).",
                cantidad_por_defecto=1000,
                imagen="bolsas-con-m.svg",
                slug="bolsas-kraft-marron-manija-cordon"
            ),
            ArticuloCatalogo(
                id=4,
                nombre="Bolsas de Papel Blanco con Manija Cordón",
                descripcion="Gramaje: 100 gr/m² | Manija cordón retorcido de papel. Premium y elegantes. Lisas, personalizadas (1 o 2 colores) o cuatricromía (para grandes cantidades).",
                cantidad_por_defecto=1000,
                imagen="bolsas-con-m.svg",
                slug="bolsas-blancas-manija-cordon"
            )
        ]

    def obtener_todos(self) -> list[ArticuloCatalogo]:
        return self._articulos

    def obtener_por_id(self, id_articulo: int) -> ArticuloCatalogo | None:
        return next((p for p in self._articulos if p.id == id_articulo), None)

    def obtener_por_slug(self, slug: str) -> ArticuloCatalogo | None:
        return next((p for p in self._articulos if p.url_slug == slug), None)

    def buscar(self, query: str) -> list[ArticuloCatalogo]:
        query_filtrada = query.strip().lower()
        if not query_filtrada:
            return self._articulos
        return [
            p for p in self._articulos
            if query_filtrada in p.nombre.lower() or query_filtrada in p.descripcion.lower()
        ]
