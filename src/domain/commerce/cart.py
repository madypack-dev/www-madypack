from pydantic import BaseModel, Field, field_validator


class CalculoArticulo(BaseModel):
    """Configuración de cálculo de precio para un artículo del catálogo.

    Permite definir, por artículo, qué conceptos de tarifa se usan y con qué
    estrategia se calcula el precio estimado.
    """

    model_config = {"frozen": True}

    tipo: str
    conceptos: list[str]
    concepto_fijo: str | None = None



class ArticuloCarrito(BaseModel):
    model_config = {"validate_assignment": True}

    id: int
    nombre: str
    descripcion: str
    cantidad: int = Field(..., ge=100)
    imagen: str
    calculo: CalculoArticulo | None = None
    unidad: str = Field(default="unidades")

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

    @property
    def total_lineas(self) -> int:
        return len(self.articulos)

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
