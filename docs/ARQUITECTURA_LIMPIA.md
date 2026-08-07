# Arquitectura Limpia — Guardia AST de Dependencias

Este documento describe las reglas de dependencia entre capas que el proyecto impone mediante el script `scripts/check_clean_architecture.py`, y los principios de diseño que las motivan.

---

## Principios

El diseño sigue tres principios fundamentales:

1. **Regla de Dependencia (DDD / Uncle Bob)**: las dependencias de código fuente solo pueden apuntar hacia adentro. Las capas internas no conocen nada de las capas externas.
2. **Screaming Architecture**: la estructura de directorios grita la intención del sistema. `src/domain/`, `src/application/`, `src/adapters/`, `src/infrastructure/` comunican exactamente qué es el proyecto.
3. **SOLID**: en particular el Principio de Inversión de Dependencias (DIP). Las capas internas definen puertos (interfaces), las capas externas los implementan.

---

## Estructura de capas

```
src/
├── domain/           # Capa más interna: entidades, value objects, puertos
├── application/      # Casos de uso, servicios de aplicación
├── adapters/         # Implementaciones de puertos del dominio
└── infrastructure/   # Capa más externa: FastAPI, httpx, ReportLab, etc.
```

**Flecha de dependencia permitida**:

```
domain ← application ← adapters ← infrastructure
```

---

## Reglas por capa

### `src/domain/` — El Dominio

**No puede importar nada de**:
- `src.application`, `src.adapters`, `src.infrastructure`
- `fastapi`, `starlette` (frameworks web)
- `httpx` (cliente HTTP)
- `reportlab` (generación de PDFs)
- `jinja2` (templating)
- `structlog` (logging estructurado)

**Puede importar**: solo la biblioteca estándar de Python y otras clases dentro de `src/domain/`.

### `src/application/` — La Aplicación

**No puede importar nada de**:
- `src.adapters`, `src.infrastructure`
- `fastapi`, `starlette`, `httpx`, `reportlab`, `jinja2`

**Puede importar**: `src.domain`, stdlib.

### `src/adapters/` — Los Adaptadores

**No puede importar nada de**:
- `src.infrastructure`
- `fastapi`
- `httpx`

**Puede importar**: `src.domain`, `src.application`, stdlib, y librerías externas que no sean de infraestructura web.

### `src/infrastructure/` — La Infraestructura

**No evaluada por la guardia**. Es la capa más externa y puede depender de cualquier cosa: frameworks, librerías, y todas las capas internas.

---

## Reglas globales

### Prohibición de importaciones relativas

```python
# ❌ PROHIBIDO
from .calculator import calcular_precio
from ..entities import Producto

# ✅ CORRECTO
from src.domain.pricing.calculator import calcular_precio
from src.domain.erp.entities import Producto
```

Todas las importaciones deben ser absolutas empezando con `from src...`. Esto elimina la ambigüedad sobre qué módulo se está importando y hace que los imports sean resistentes a refactorizaciones.

### Archivos `__init__.py` vacíos

Todos los `__init__.py` bajo `src/` deben tener **0 bytes**. Esto evita el acoplamiento temprano que ocurre cuando un `__init__.py` re-exporta símbolos.

```python
# ❌ PROHIBIDO en __init__.py
from .calculator import CotizadorServicio

# ✅ CORRECTO: __init__.py completamente vacío
```

---

## Cómo funciona la guardia

`scripts/check_clean_architecture.py` analiza el **AST** (Abstract Syntax Tree) de cada archivo `.py` bajo `src/` sin ejecutar código:

1. Para cada capa definida en `FORBIDDEN_IMPORTS`, recorre recursivamente los `.py`
2. Para cada archivo, parsea el AST y busca nodos `import` e `import from`
3. Compara cada nombre de módulo importado contra la lista de prefijos prohibidos para esa capa
4. Detecta importaciones relativas (`from .`) por el atributo `level > 0` en nodos `ImportFrom`
5. Verifica que `__init__.py` tenga tamaño 0 bytes

El script retorna **exit code 1** si encuentra cualquier violación.

---

## Cómo agregar una nueva regla

Para prohibir una nueva librería o prefijo en una capa, editar `FORBIDDEN_IMPORTS` en `scripts/check_clean_architecture.py`:

```python
"src/domain": {
    "forbidden_prefixes": (
        "src.application",
        "src.adapters",
        # ... existentes ...
        "requests",       # ← nueva librería prohibida
    ),
    "rule_description": "El Dominio no debe depender de capas externas ni de frameworks.",
},
```

---

## Integración con CI

La guardia se ejecuta en el Paso 1 de `./scripts/CI.sh`. También hay tests BDD en `tests/features/test_clean_architecture_steps.py` que validan las mismas reglas desde la suite de pytest.

---

## Violaciones comunes y soluciones

| Violación | Causa típica | Solución |
|---|---|---|
| `src.adapters/` importa `src.infrastructure` | El adaptador depende de config o logger de infraestructura | Inyectar configuración y logger por constructor |
| `src.adapters/` importa `httpx` | El adaptador usa httpx directamente | Usar el puerto `IHttpClient` de dominio |
| `src/domain/` importa `structlog` | El dominio quiere loguear | El dominio no debe loguear; lanzar excepciones que la capa superior capture y loguee |
| `from . import X` | Import relativo por comodidad | Cambiar a `from src.carpeta.modulo import X` |
| `__init__.py` no vacío | Re-exporta símbolos para acortar imports | Eliminar el contenido; usar imports explícitos completos |
