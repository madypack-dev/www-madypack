# Mutation Testing con mutmut

Este documento describe la configuración, problemas conocidos y estado actual del mutation testing en el proyecto usando [mutmut](https://github.com/boxed/mutmut).

---

## ¿Qué es mutation testing?

El mutation testing introduce bugs artificiales ("mutantes") en el código fuente y verifica que los tests los detecten. Si un mutante sobrevive (los tests pasan a pesar del bug), hay un punto ciego en la suite de pruebas.

Ejemplo de mutación en `calculator.py`:

```python
# Código original
if cantidad > 0:
    ...

# Mutante (cambio de operador)
if cantidad >= 0:
    ...
```

Si los tests NO fallan con este cambio, hay cobertura de línea pero no cobertura lógica.

---

## Configuración actual

```toml
# pyproject.toml
[tool.mutmut]
source_paths = ["src/domain/pricing/"]
runner = "../venv/bin/python -m pytest -o pythonpath=src:. --no-cov tests/pricing"
```

- **`source_paths`**: solo se muta `src/domain/pricing/` (3 archivos: `calculator.py`, `conversor_moneda.py`, `actualizador_ipc.py`)
- **`runner`**: comando que ejecuta los tests para cada mutante. Se ejecuta desde dentro del directorio `mutants/`

### ¿Por qué `pythonpath=src:.` sin `..`?

El orden en `pythonpath` es crítico:

```
pythonpath=src:.     # ✅ CORRECTO: mutants/src/ (mutado) antes que mutants/
pythonpath=..:src:.  # ❌ INCORRECTO: raíz real antes que código mutado
```

Si la raíz real aparece antes que `mutants/src/`, Python resuelve `from src.domain.pricing...` al código **original sin mutar**, y todos los mutantes sobreviven espuriamente.

### Soporte en `tests/conftest.py`

El `conftest.py` detecta si se está ejecutando desde el directorio `mutants/` y ajusta `sys.path`:

```python
_en_mutants = os.path.basename(root_dir) == "mutants"
if _en_mutants:
    root_dir = os.path.abspath(os.path.join(root_dir, ".."))

if root_dir not in sys.path:
    if _en_mutants:
        sys.path.append(root_dir)   # ← append, no insert(0)
    else:
        sys.path.insert(0, root_dir)
```

En modo normal, la raíz del proyecto se inserta al inicio de `sys.path`. En modo mutmut, se **appendea al final**, para que `mutants/src/` (inyectado por `pythonpath=src:.`) tenga prioridad sobre el código real.

---

## Problemas conocidos

### 1. Incompatibilidad de mutmut 3.7.0 con layout `src/`

**Síntoma**:
```
AssertionError: Failed trampoline hit. Module name starts with `src.`, which is invalid
```

**Causa**: mutmut 3.7.0 tiene un `assert` en `__main__.py:123` que rechaza cualquier módulo cuyo nombre empiece con `src.`. Esto impide usar mutmut con el layout estándar `src/` donde el paquete top-level es `src`.

**Parche aplicado**: se comentó la aserción en `venv/lib/python3.12/site-packages/mutmut/__main__.py:122-125`:

```python
def record_trampoline_hit(name: str, caller: str | None = None) -> None:
    # Parche: el layout src/ es válido en arquitectura limpia; la aserción original
    # impedía usar mutmut con proyectos que usan "src" como paquete top-level.
    # assert not name.startswith("src."), ...
```

**Impacto del parche**: cada vez que se recrea el venv (`pip install`), el parche debe re-aplicarse. Ver sección "Re-aplicar el parche" más abajo.

### 2. Fase de recolección de stats ejecuta TODOS los tests

**Síntoma**: durante `mutmut run`, la fase "Running stats" falla con:
```
FAILED tests/customization/test_customization.py::test_get_personalizar_renderiza_ok
jinja2.exceptions.TemplateNotFound: 'pages/personalizar.html' not found in search path: 'templates'
```

**Causa**: mutmut copia `src/` y `tests/` al directorio `mutants/`, pero **no copia `templates/`**. La fase de recolección de stats ejecuta TODOS los tests para mapear cobertura, y los tests de `customization` requieren templates que no existen en `mutants/`.

**Soluciones posibles** (no implementadas aún):

| Opción | Descripción | Trade-off |
|---|---|---|
| A | Agregar `pytest_add_cli_args = ["--ignore=tests/customization"]` a `[tool.mutmut]` | Fácil, pero requiere mantener la lista de tests ignorados |
| B | Crear symlink `mutants/templates -> ../templates` antes de mutmut | Requiere wrapper script |
| C | Evaluar otra herramienta (ej. `cosmic-ray`, `mut.py`) | Mayor esfuerzo de migración |

---

## Cómo ejecutar

```bash
# Limpiar artefactos de corridas anteriores
rm -rf mutants/ .mutmut-cache/

# Ejecutar mutation testing
./venv/bin/mutmut run src/domain/pricing/

# Ver resultados
./venv/bin/mutmut results
```

Incluido en CI como Paso 6 de `./scripts/CI.sh` (se omite con `--fast`).

---

## Re-aplicar el parche después de reconstruir el venv

```bash
# Localizar el archivo
MUTMUT_MAIN=$(./venv/bin/python -c "import mutmut; print(mutmut.__file__.replace('__init__.py','__main__.py'))")

# Aplicar parche
sed -i 's/    assert not name.startswith("src."), "Failed trampoline hit.*/    # Parche: layout src\/ valido en arquitectura limpia/' "$MUTMUT_MAIN"
```

---

## Tests de pricing (4 tests)

Archivo: `tests/pricing/test_conversor_moneda.py`

| Test | Qué valida |
|---|---|
| `test_concepto_ars_no_se_convierte` | Los conceptos en ARS no se modifican |
| `test_concepto_usd_se_convierte_a_ars` | Los conceptos en USD se convierten usando la tasa de cambio |
| `test_mezcla_de_monedas_se_convierte_correctamente` | Cotización mixta (ARS + USD) produce totales correctos |
| `test_concepto_inexistente_en_diccionario_no_aparece` | Conceptos sin datos en el diccionario se omiten silenciosamente |

---

## Referencias

- [mutmut en GitHub](https://github.com/boxed/mutmut)
- [Mutation Testing — Martin Fowler](https://martinfowler.com/bliki/MutationTesting.html)
- [Python `src` layout — PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
