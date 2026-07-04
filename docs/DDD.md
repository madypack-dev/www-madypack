# Arquitectura por Capas

Este documento describe la arquitectura actual del proyecto desde la perspectiva de **Domain-Driven Design (DDD)**, **Arquitectura Limpia** y los **principios SOLID**.

El objetivo es mantener el **dominio y la lógica de negocio desacoplados** de los detalles de infraestructura (FastAPI, cookies, archivos YAML, etc.).

---

## 1. Visión General de Capas

```text
┌─────────────────────────────────────┐
│        Infraestructura              │  FastAPI, rutas, plantillas,
│   src/infraestructura/              │  resolución de tenant, carga de YAML
├─────────────────────────────────────┤
│          Adaptadores                │  Implementaciones concretas de
│  src/comercio/adaptadores/          │  puertos (repositorios, servicios)
│  src/precios/adaptadores/           │
├─────────────────────────────────────┤
│         Casos de Uso                │  Orquestación del flujo de negocio
│   src/comercio/aplicacion/          │
├─────────────────────────────────────┤
│            Dominio                  │  Entidades, value objects y puertos
│   src/comercio/dominio/             │  Libres de dependencias externas
│   src/precios/dominio/              │
└─────────────────────────────────────┘
```

Las dependencias apuntan siempre hacia el centro: la infraestructura depende de los adaptadores, los adaptadores implementan los puertos del dominio, y los casos de uso orquestan el dominio.

---

## 2. Capa de Dominio

Contiene las entidades, value objects y puertos (interfaces). No tiene dependencias de frameworks ni de detalles de persistencia.

### `src/comercio/dominio/modelos/carrito.py`

```python
class ArticuloCarrito(BaseModel):
    id: int
    nombre: str
    descripcion: str
    cantidad: int = Field(..., ge=100)
    imagen: str
```

* `ArticuloCarrito` encapsula la regla de que la cantidad mínima es 100 y debe ser múltiplo de 100.
* `Carrito` gestiona la colección de artículos y calcula el total de bolsas.

### `src/comercio/dominio/puertos/repositorio.py`

```python
class IRepositorioCarrito(ABC):
    @abstractmethod
    def obtener_carrito(self) -> Carrito: ...
    @abstractmethod
    def guardar_carrito(self, carrito: Carrito) -> None: ...
```

El dominio no sabe si el carrito se guarda en una cookie, una base de datos o una sesión. Esa decisión pertenece a la capa de adaptadores.

### `src/precios/dominio/modelos/tarifas.py`

Modela las tarifas de cotización como value objects tipados con Pydantic.

---

## 3. Capa de Aplicación

Orquesta los casos de uso sin contener lógica de negocio propia.

### `src/comercio/aplicacion/casos_uso/carrito.py`

* `CasoUsoAgregarAlCarrito`: busca el producto en el catálogo, instancia un `ArticuloCarrito` y lo agrega al carrito.
* `CasoUsoActualizarCarrito`: actualiza las cantidades de los artículos existentes.

Ambos reciben un `registrar_error: Callable[[str], None]` para no depender del logger de infraestructura.

---

## 4. Capa de Adaptadores

Implementa los puertos del dominio con tecnologías concretas.

### `src/comercio/adaptadores/repositorios/cookie.py`

`RepositorioCarritoCookie` implementa `IRepositorioCarrito` usando cookies HTTP. Recibe:

* `cookies: dict[str, str]` – datos crudos de la petición.
* `cargar_defecto_yaml: Callable[[], list[dict[str, Any]]]` – fuente del catálogo.
* `registrar_error: Callable[[str], None]` – callback de logging.

No importa FastAPI; solo conoce diccionarios de Python.

### `src/precios/adaptadores/servicios/cotizador.py`

`CotizadorServicio` implementa `IServicioPrecios` y calcula precios estimados a partir de las tarifas de un tenant.

---

## 5. Capa de Infraestructura

Contiene todo lo relacionado con frameworks y detalles técnicos.

### `src/infraestructura/rutas/`

* `base.py`: configuración de templates, logging y `load_site`.
* `paginas.py`: rutas estáticas de páginas institucionales.
* `carrito.py`: rutas de tienda y carrito. Recibe el tenant resuelto, carga los YAML correspondientes y traduce HTTP a llamadas de casos de uso.

### `src/infraestructura/tenant/resolutor.py`

Resuelve el tenant según el entorno:

* **Desarrollo:** por puerto (`8000` → `default`, `8001` → `empresa-1`).
* **Staging:** por subdominio (`empresa-1.datamaq.com.ar`).
* **Producción:** por dominio propio (`empresa-1.com.ar`).

### `src/infraestructura/datos/cargadores.py`

Carga los archivos YAML de cada tenant desde `data/<tenant>/`, con fallback a `data/default/` si un archivo no existe.

---

## 6. Análisis SOLID

### S – Single Responsibility Principle

Cada capa tiene una responsabilidad clara:

* El dominio define reglas.
* Los casos de uso orquestan.
* Los adaptadores implementan puertos.
* La infraestructura maneja HTTP.

### O – Open/Closed Principle

Nuevos medios de persistencia (base de datos, Redis) pueden agregarse implementando `IRepositorioCarrito` sin modificar el dominio ni los casos de uso.

### L – Liskov Substitution Principle

`RepositorioCarritoCookie` y `CotizadorServicio` pueden sustituir a sus respectivas abstracciones (`IRepositorioCarrito`, `IServicioPrecios`) sin alterar el comportamiento esperado.

### I – Interface Segregation Principle

Los puertos son pequeños y específicos: `IRepositorioCarrito` solo tiene dos métodos.

### D – Dependency Inversion Principle

Los casos de uso dependen de abstracciones (`IRepositorioCarrito`), no de implementaciones concretas. La infraestructura inyecta las implementaciones.

---

## 7. Multi-Tenant

La arquitectura multi-tenant se implementa en infraestructura. El dominio y los casos de uso no conocen el concepto de tenant; solo reciben los datos que la infraestructura les proporciona.

Ver [docs/multi-tenant.md](docs/multi-tenant.md) para más detalles.

---

## 8. Próximas Mejoras

* Agregar tests unitarios para dominio y casos de uso.
* Evaluar el uso de un contenedor de dependencias o inyección más explícita.
* Considerar cachear los YAML en memoria para reducir lecturas de disco.
