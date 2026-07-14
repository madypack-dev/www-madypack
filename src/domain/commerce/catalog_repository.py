from abc import ABC, abstractmethod

from src.domain.commerce.catalog import VariacionProducto
from src.domain.commerce.product import ComponenteBien, Producto, ProductoBien, ProductoServicio


class ICatalogRepository(ABC):
    """Interfaz (puerto) para el catálogo de bienes, servicios y compuestos."""

    @abstractmethod
    def obtener_todos(self) -> list[Producto]:
        """Obtiene la lista completa de productos del catálogo."""
        pass

    @abstractmethod
    def obtener_por_id(self, id_producto: int) -> Producto | None:
        """Busca un producto por su ID numérico."""
        pass

    @abstractmethod
    def obtener_por_slug(self, slug: str) -> Producto | None:
        """Busca un producto por su slug único."""
        pass

    @abstractmethod
    def buscar(self, query: str) -> list[Producto]:
        """Busca productos que coincidan con la consulta en su nombre o descripción."""
        pass

    @abstractmethod
    def obtener_variacion_por_id(
        self, id_variacion: int
    ) -> tuple[ProductoBien, VariacionProducto] | None:
        """Busca una variación específica y su bien asociado por el ID de la variación."""
        pass

    @abstractmethod
    def obtener_servicio_por_id(self, id_servicio: int) -> ProductoServicio | None:
        """Busca un servicio por su ID numérico."""
        pass

    @abstractmethod
    def resolver_componente(
        self, componente: ComponenteBien
    ) -> VariacionProducto | ProductoServicio | None:
        """Resuelve un componente de bien a su variación o servicio correspondiente."""
        pass
