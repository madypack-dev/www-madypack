from abc import ABC, abstractmethod

from src.domain.comercio.cart import Carrito


class IRepositorioCarrito(ABC):
    @abstractmethod
    def obtener_carrito(self) -> Carrito:
        pass

    @abstractmethod
    def guardar_carrito(self, carrito: Carrito) -> None:
        pass
