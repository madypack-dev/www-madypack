# Plan de Refactorización Refinado: Desacoplamiento de Adaptadores

> **Obsoleto**
>
> Este documento describe una propuesta de estructura de carpetas (`src/dominio/`, `src/aplicacion/`, `src/adaptadores/`)
> que **no fue implementada** tal cual. El código real mantiene los bounded contexts en `src/comercio/`, `src/precios/`,
> `src/lead/` y `src/presupuesto/`, cada uno con su propia capa de dominio/aplicación/adaptadores.
> Queda archivado como referencia histórica.

Este plan refina el diseño para asegurar que la capa de **Adaptadores** sea completamente agnóstica a detalles de infraestructura (como el framework FastAPI).

### Cambios Arquitectónicos Clave:
* **Adaptador Puro:** `RepositorioCarritoCookie` ya no importa ni depende de `fastapi.Request`. En su lugar, interactúa con un diccionario estándar de Python (`dict[str, str]`) para procesar las cookies.
* **Aislamiento del Framework:** El controlador de FastAPI (Infraestructura) se encarga de extraer las cookies de la petición HTTP y pasarlas al adaptador, así como de aplicar las modificaciones de las cookies a la respuesta HTTP.

---

## 1. Implementación por Capas

### A. Capa de Dominio (`src/dominio/`)

Contiene las entidades y reglas de negocio puras representadas mediante Pydantic, libres de dependencias externas del sistema.

#### Modelos (`src/dominio/modelos/carrito.py`)
```python
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
```

#### Puertos (`src/dominio/puertos/repositorio.py`)
```python
from abc import ABC, abstractmethod
from src.dominio.modelos.carrito import Carrito

class IRepositorioCarrito(ABC):
    @abstractmethod
    def obtener_carrito(self) -> Carrito:
        pass

    @abstractmethod
    def guardar_carrito(self, carrito: Carrito) -> None:
        pass
```

---

### B. Capa de Aplicación (`src/aplicacion/`)

Encapsula los casos de uso orquestando el dominio. El logging se inyecta mediante un callback (`registrar_error`) para no acoplar la capa al logging de infraestructura.

#### Casos de Uso (`src/aplicacion/casos_uso/carrito.py`)
```python
from typing import Callable, Any
from src.dominio.puertos.repositorio import IRepositorioCarrito
from src.dominio.modelos.carrito import ArticuloCarrito

class CasoUsoActualizarCarrito:
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda m: None):
        self.repositorio = repositorio
        self.registrar_error = registrar_error

    def ejecutar(self, actualizaciones: dict[int, int]) -> None:
        carrito = self.repositorio.obtener_carrito()
        modificado = False
        for id_articulo, nueva_cantidad in actualizaciones.items():
            try:
                if carrito.actualizar_cantidad(id_articulo, nueva_cantidad):
                    modificado = True
            except ValueError as err:
                self.registrar_error(f"Error de validación al actualizar artículo {id_articulo}: {err}")
                continue
        if modificado:
            self.repositorio.guardar_carrito(carrito)


class CasoUsoAgregarAlCarrito:
    def __init__(self, repositorio: IRepositorioCarrito, registrar_error: Callable[[str], None] = lambda m: None):
        self.repositorio = repositorio
        self.registrar_error = registrar_error

    def ejecutar(self, id_articulo: int, cantidad: int, catalogo: list[dict[str, Any]]) -> None:
        datos_producto = next((p for p in catalogo if p["id"] == id_articulo), None)
        if not datos_producto:
            self.registrar_error(f"Intento de agregar artículo inexistente del catálogo: {id_articulo}")
            raise ValueError("El artículo no existe en el catálogo.")

        carrito = self.repositorio.obtener_carrito()

        try:
            articulo = ArticuloCarrito(
                id=datos_producto["id"],
                nombre=datos_producto["nombre"],
                descripcion=datos_producto["descripcion"],
                cantidad=cantidad,
                imagen=datos_producto["imagen"]
            )
            carrito.agregar_articulo(articulo)
            self.repositorio.guardar_carrito(carrito)
        except ValueError as err:
            self.registrar_error(f"Error de validación al agregar artículo {id_articulo} al carrito: {err}")
            raise err
```

---

### C. Capa de Adaptadores (`src/adaptadores/`)

El repositorio ahora es un adaptador puro de Python. No importa FastAPI ni frameworks web externos. Se comunica únicamente usando tipos primitivos (`dict[str, str]`).

#### Repositorio de Cookies Puro (`src/adaptadores/repositorios/cookie.py`)
```python
import json
from typing import Callable, Any
from src.dominio.modelos.carrito import Carrito, ArticuloCarrito
from src.dominio.puertos.repositorio import IRepositorioCarrito

class RepositorioCarritoCookie(IRepositorioCarrito):
    def __init__(
        self, 
        cookies: dict[str, str], 
        cargar_defecto_yaml: Callable[[], list[dict[str, Any]]],
        nombre_cookie: str = "articulos_carrito",
        registrar_error: Callable[[str], None] = lambda m: None
    ):
        self.cookies = cookies
        self.cargar_defecto_yaml = cargar_defecto_yaml
        self.nombre_cookie = nombre_cookie
        self.registrar_error = registrar_error
        self._carrito_serializado: str | None = None

    def obtener_carrito(self) -> Carrito:
        valor_cookie = self.cookies.get(self.nombre_cookie)
        if valor_cookie:
            try:
                datos = json.loads(valor_cookie)
                articulos = [ArticuloCarrito(**item) for item in datos]
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
```

---

### D. Capa de Infraestructura (`src/infraestructura/`)

El controlador FastAPI (capa externa) es el encargado de interactuar con la petición y respuesta HTTP, abstrayendo estas particularidades antes de instanciar los componentes del sistema.

#### Controlador de FastAPI (`src/infraestructura/rutas/carrito.py`)
```python
from pathlib import Path
import yaml
import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infraestructura.routes.base import templates, load_site, LoggingRoute, logger
from src.adaptadores.repositorios.cookie import RepositorioCarritoCookie
from src.aplicacion.casos_uso.carrito import CasoUsoActualizarCarrito, CasoUsoAgregarAlCarrito

router = APIRouter(route_class=LoggingRoute)

PATH_CARRITO_YAML = Path(__file__).resolve().parents[3] / "data" / "productos_tienda.yml"

def obtener_catalogo_productos() -> list[dict]:
    if not PATH_CARRITO_YAML.exists():
        logger.error(f"No se encontró el catálogo YAML en: {PATH_CARRITO_YAML}")
        return []
    try:
        contenido = yaml.safe_load(PATH_CARRITO_YAML.read_text(encoding="utf-8"))
        return contenido.get("articulos", [])
    except Exception as err:
        logger.error(f"Error parseando catálogo de productos: {err}", exc_info=True)
        return []


@router.get("/tienda/", response_class=HTMLResponse)
async def ver_tienda(request: Request, sitio: dict = Depends(load_site)):
    catalogo = obtener_catalogo_productos()
    return templates.TemplateResponse(
        request=request,
        name="pages/tienda.html",
        context={"site": sitio, "productos": catalogo}
    )


@router.post("/carrito/agregar")
async def agregar_al_carrito(
    request: Request,
    id_articulo: int = Form(...),
    cantidad: int = Form(...)
):
    # Pasamos únicamente request.cookies (un dict estándar) al adaptador de repositorio
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    
    caso_uso = CasoUsoAgregarAlCarrito(
        repositorio=repositorio,
        registrar_error=logger.error
    )
    
    try:
        catalogo = obtener_catalogo_productos()
        caso_uso.ejecutar(id_articulo, cantidad, catalogo)
        logger.info(f"Artículo {id_articulo} agregado al carrito con cantidad {cantidad}")
    except ValueError as err:
        logger.error(f"Error al agregar artículo {id_articulo} al carrito: {err}")
        return RedirectResponse(url="/tienda/?error=cantidad_invalida", status_code=303)

    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    
    # Manejamos el set_cookie aquí en infraestructura
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600*24*30,
            path="/"
        )
    return respuesta


@router.get("/carrito/", response_class=HTMLResponse)
async def ver_carrito(request: Request, sitio: dict = Depends(load_site)):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    carrito = repositorio.obtener_carrito()
    
    total_bolsas_formateado = f"{carrito.total_bolsas:,} unidades".replace(",", ".")
    
    return templates.TemplateResponse(
        request=request,
        name="pages/carrito.html",
        context={
            "site": sitio,
            "cart_items": carrito.articulos,
            "total_bags_formatted": total_bolsas_formateado
        },
    )


@router.post("/carrito/actualizar")
async def actualizar_carrito(request: Request):
    datos_formulario = await request.form()
    
    actualizaciones = {}
    for clave, valor in datos_formulario.items():
        if clave.startswith("qty_"):
            try:
                id_articulo = int(clave.replace("qty_", ""))
                actualizaciones[id_articulo] = int(valor)
            except ValueError:
                continue

    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    
    caso_uso = CasoUsoActualizarCarrito(
        repositorio=repositorio,
        registrar_error=logger.error
    )
    caso_uso.ejecutar(actualizaciones)
    
    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600*24*30,
            path="/"
        )
    return respuesta
```
