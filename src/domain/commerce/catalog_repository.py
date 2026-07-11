from abc import ABC, abstractmethod
from src.domain.commerce.catalog import ArticuloCatalogo

class ICatalogRepository(ABC):
    """Interfaz (puerto) para el catálogo de artículos."""

    @abstractmethod
    def obtener_todos(self) -> list[ArticuloCatalogo]:
        """Obtiene la lista completa de artículos del catálogo."""
        pass

    @abstractmethod
    def obtener_por_id(self, id_articulo: int) -> ArticuloCatalogo | None:
        """Busca un artículo por su ID numérico."""
        pass

    @abstractmethod
    def obtener_por_slug(self, slug: str) -> ArticuloCatalogo | None:
        """Busca un artículo por su slug único."""
        pass

    @abstractmethod
    def buscar(self, query: str) -> list[ArticuloCatalogo]:
        """Busca artículos que coincidan con la consulta en su nombre o descripción."""
        pass
