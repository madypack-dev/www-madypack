from abc import ABC, abstractmethod
from src.domain.commerce.catalog import ProductoVariable, VariacionProducto


class ICatalogRepository(ABC):
    """Interfaz (puerto) para el catálogo de artículos."""

    @abstractmethod
    def obtener_todos(self) -> list[ProductoVariable]:
        """Obtiene la lista completa de productos variables del catálogo."""
        pass

    @abstractmethod
    def obtener_por_id(self, id_producto: int) -> ProductoVariable | None:
        """Busca un producto variable por su ID numérico."""
        pass

    @abstractmethod
    def obtener_por_slug(self, slug: str) -> ProductoVariable | None:
        """Busca un producto variable por su slug único."""
        pass

    @abstractmethod
    def buscar(self, query: str) -> list[ProductoVariable]:
        """Busca productos variables que coincidan con la consulta en su nombre o descripción."""
        pass

    @abstractmethod
    def obtener_variacion_por_id(
        self, id_variacion: int
    ) -> tuple[ProductoVariable, VariacionProducto] | None:
        """Busca una variación específica y su producto variable asociado por el ID de la variación."""
        pass
