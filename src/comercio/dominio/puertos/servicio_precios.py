from abc import ABC, abstractmethod

from src.comercio.dominio.modelos.carrito import ArticuloCarrito


class IServicioPrecios(ABC):
    @abstractmethod
    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        pass
