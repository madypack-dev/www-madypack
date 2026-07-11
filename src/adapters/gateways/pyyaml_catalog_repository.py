from typing import Callable, Any
from src.domain.commerce.catalog import ArticuloCatalogo
from src.domain.commerce.catalog_repository import ICatalogRepository

class YamlCatalogRepository(ICatalogRepository):
    """Implementación de ICatalogRepository para cargar productos desde archivos YAML."""

    def __init__(self, cargar_catalogo_yaml: Callable[[], Any]):
        self.cargar_catalogo_yaml = cargar_catalogo_yaml

    def obtener_todos(self) -> list[ArticuloCatalogo]:
        try:
            return self.cargar_catalogo_yaml().articulos
        except Exception:
            return []

    def obtener_por_id(self, id_articulo: int) -> ArticuloCatalogo | None:
        articulos = self.obtener_todos()
        return next((p for p in articulos if p.id == id_articulo), None)

    def obtener_por_slug(self, slug: str) -> ArticuloCatalogo | None:
        articulos = self.obtener_todos()
        return next((p for p in articulos if p.url_slug == slug), None)

    def buscar(self, query: str) -> list[ArticuloCatalogo]:
        articulos = self.obtener_todos()
        query_filtrada = query.strip().lower()
        if not query_filtrada:
            return articulos
        return [
            p for p in articulos
            if query_filtrada in p.nombre.lower() or query_filtrada in p.descripcion.lower()
        ]
