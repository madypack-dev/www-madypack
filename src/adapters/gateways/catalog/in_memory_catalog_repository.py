from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import ComponenteBien, Producto, ProductoBien, ProductoServicio

from src.adapters.gateways.catalog.catalog_seed import construir_catalogo


class InMemoryCatalogRepository(ICatalogRepository):
    def __init__(self) -> None:
        productos, variaciones, servicios = construir_catalogo()
        self._productos: list[Producto] = productos
        self._variaciones: dict[int, tuple[ProductoBien, VariacionProducto]] = variaciones
        self._servicios: dict[int, ProductoServicio] = servicios

    def obtener_todos(self) -> list[Producto]:
        return self._productos

    def obtener_por_id(self, id_producto: int) -> Producto | None:
        return next((p for p in self._productos if p.id == id_producto), None)

    def obtener_por_slug(self, slug: str) -> Producto | None:
        return next((p for p in self._productos if p.url_slug == slug), None)

    def buscar(self, query: str) -> list[Producto]:
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
