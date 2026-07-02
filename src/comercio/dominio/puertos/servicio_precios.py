from abc import ABC, abstractmethod

class IServicioPrecios(ABC):
    @abstractmethod
    def calcular_precio_estimado(self, id_articulo: int, cantidad: int) -> float:
        pass
