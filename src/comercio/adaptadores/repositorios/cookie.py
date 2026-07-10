import json
from typing import Callable
from src.comercio.dominio.modelos.carrito import Carrito, ArticuloCarrito
from src.comercio.dominio.puertos.repositorio import IRepositorioCarrito


class RepositorioCarritoCookie(IRepositorioCarrito):
    def __init__(
        self,
        cookies: dict[str, str],
        nombre_cookie: str = "articulos_carrito",
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.cookies = cookies
        self.nombre_cookie = nombre_cookie
        self.registrar_error = registrar_error
        self._carrito_serializado: str | None = None

    def obtener_carrito(self) -> Carrito:
        valor_cookie = self.cookies.get(self.nombre_cookie)
        if valor_cookie:
            try:
                datos = json.loads(valor_cookie)
                if isinstance(datos, list):
                    articulos = [ArticuloCarrito(**item) for item in datos]
                elif isinstance(datos, dict):
                    articulos = [ArticuloCarrito(**item) for item in datos.get("articulos", [])]
                else:
                    articulos = []
                return Carrito(articulos=articulos)
            except Exception as err:
                self.registrar_error(f"Error al deserializar cookie de carrito: {err}")
                
        # Si no hay cookie, devolvemos un carrito vacío
        return Carrito(articulos=[])

    def guardar_carrito(self, carrito: Carrito) -> None:
        self._carrito_serializado = carrito.model_dump_json()

    @property
    def carrito_serializado(self) -> str | None:
        return self._carrito_serializado
