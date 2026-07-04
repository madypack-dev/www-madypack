from pydantic import BaseModel, Field, field_validator

class ArticuloCarrito(BaseModel):
    id: int
    nombre: str
    descripcion: str
    cantidad: int = Field(..., ge=100)
    imagen: str

    @field_validator("cantidad")
    @classmethod
    def validar_cantidad_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad debe ser múltiplo de 100.")
        return valor


class Carrito(BaseModel):
    articulos: list[ArticuloCarrito] = []

    @property
    def total_bolsas(self) -> int:
        return sum(articulo.cantidad for articulo in self.articulos)

    def actualizar_cantidad(self, id_articulo: int, nueva_cantidad: int) -> bool:
        for articulo in self.articulos:
            if articulo.id == id_articulo:
                articulo.cantidad = nueva_cantidad
                return True
        return False

    def agregar_articulo(self, nuevo_articulo: ArticuloCarrito) -> None:
        for articulo in self.articulos:
            if articulo.id == nuevo_articulo.id:
                articulo.cantidad += nuevo_articulo.cantidad
                return
        self.articulos.append(nuevo_articulo)

    def eliminar_articulo(self, id_articulo: int) -> bool:
        for indice, articulo in enumerate(self.articulos):
            if articulo.id == id_articulo:
                self.articulos.pop(indice)
                return True
        return False
