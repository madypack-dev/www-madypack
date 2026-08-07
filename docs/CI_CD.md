# Pipeline de Integración Continua — Gauntlet del Tío Bob

Este documento describe el pipeline `./scripts/CI.sh`, conocido como el **Gauntlet del Tío Bob**, que automatiza la verificación de calidad, arquitectura y seguridad del proyecto Madypack.

---

## Ejecución

```bash
# Pipeline completo (6 pasos, incluyendo mutation testing)
./scripts/CI.sh

# Pipeline rápido (5 pasos, sin mutation testing)
./scripts/CI.sh --fast
```

El script usa `set -eo pipefail`: cualquier paso que falle aborta la ejecución inmediatamente.

---

## Paso 0 — Compilación CSS Bundle

```bash
./venv/bin/python -m src.infrastructure.tailwindcss.css_bundle
```

Compila los estilos Tailwind CSS en `static/css/bundle.css` para que estén disponibles en el sistema de archivos durante las pruebas que renderizan templates.

---

## Paso 1 — Guardia de Arquitectura Limpia (AST)

```bash
./venv/bin/python scripts/check_clean_architecture.py
```

Valida estáticamente (sin ejecutar código) que las importaciones entre capas respeten la **regla de dependencia**:

| Capa | Puede depender de |
|---|---|
| `src/domain/` | Solo Python stdlib |
| `src/application/` | `src.domain` |
| `src/adapters/` | `src.domain`, `src.application` |
| `src/infrastructure/` | Todas las capas (no evaluada) |

**Reglas adicionales**:
- Prohibidas las importaciones relativas (`from .`). Solo `from src...`.
- Todos los `__init__.py` bajo `src/` deben estar vacíos (0 bytes).

Ver [`docs/ARQUITECTURA_LIMPIA.md`](ARQUITECTURA_LIMPIA.md) para más detalles.

---

## Paso 2 — Ruff (Linting + Formateo + Complejidad Ciclomática)

```bash
./venv/bin/ruff check src/ tests/
```

Ejecuta el linter Ruff con las reglas definidas en `pyproject.toml`:

- `E`, `F`, `W`: errores y warnings estándar (pyflakes, pycodestyle)
- `C90`: complejidad ciclomática (`max-complexity = 7`)
- `I`: ordenamiento de imports (isort)
- `N`: convenciones de nombres (pep8-naming)
- `UP`: actualizaciones de sintaxis moderna
- `B`: chequeo de bugs potenciales (flake8-bugbear)

**Exclusiones**: `E501` (longitud de línea, delegada al formateador), `B008` (parámetros por defecto en FastAPI Depends), `N815` (nombres en modelos Pydantic).

---

## Paso 3 — Mypy (Tipado Estático)

```bash
./venv/bin/mypy src/domain src/application
```

Verifica tipos estáticos **solo en las capas de dominio y aplicación**. La configuración en `pyproject.toml` (`[tool.mypy]`) exige:

- `disallow_untyped_defs = true`: todas las funciones deben tener anotaciones de tipo
- `disallow_incomplete_defs = true`: no se permiten anotaciones parciales
- `warn_return_any = true`: advierte si una función tipada retorna `Any`

Las librerías externas sin stubs (`reportlab`, `PIL`, `yaml`, `structlog`, etc.) tienen `ignore_missing_imports = true`.

---

## Paso 4 — Bandit (Seguridad) + Vulture (Código Muerto)

```bash
./venv/bin/bandit -q -r src/ -s B110,B603,B607,B404
./venv/bin/vulture src/ --min-confidence 80
```

- **Bandit**: auditoría de seguridad estática. Se excluyen `B110` (try/except), `B603`/`B607` (subprocess sin shell, usado por mutmut), `B404` (subprocess import).
- **Vulture**: detección de código muerto con confianza ≥ 80%.

---

## Paso 5 — Pytest + BDD + Cobertura

```bash
./venv/bin/pytest
```

Ejecuta **180 tests** con:

- **pytest-asyncio** en modo `strict` (todas las corrutinas deben estar marcadas con `@pytest.mark.asyncio`)
- **pytest-bdd** para tests Gherkin
- **pytest-cov** con `--cov=src --cov-branch --cov-fail-under=85`

**Umbral de cobertura**: 85% (rama). La cobertura actual ronda ~87%.

Configuración consolidada en `pyproject.toml` bajo `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
pythonpath = "."
testpaths = ["tests"]
norecursedirs = ["mutants", ".mutmut-cache", ".venv", "venv"]
asyncio_mode = "strict"
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=85 --cov-branch"
```

> **Nota histórica**: antes existía un archivo `pytest.ini` duplicado que causaba conflicto de configuración (umbral de cobertura downgradeado silenciosamente de 88 a 85). Se consolidó todo en `pyproject.toml` y se eliminó `pytest.ini`.

---

## Paso 6 — Mutation Testing (mutmut)

```bash
./venv/bin/mutmut run src/domain/pricing/
```

Verifica la calidad de los tests de dominio de pricing mediante **mutation testing**: mutmut introduce bugs artificiales (mutantes) en `src/domain/pricing/` y verifica que los tests los detecten.

Este paso se **omite** con el flag `--fast`.

Configuración en `pyproject.toml`:

```toml
[tool.mutmut]
source_paths = ["src/domain/pricing/"]
runner = "../venv/bin/python -m pytest -o pythonpath=src:. --no-cov tests/pricing"
```

> **Nota**: mutmut 3.7.0 es incompatible con el layout `src/`. Ver [`docs/MUTATION_TESTING.md`](MUTATION_TESTING.md) para detalles del parche aplicado y problemas conocidos.

---

## Resumen de configuración

| Herramienta | Archivo | Sección |
|---|---|---|
| Ruff | `pyproject.toml` | `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.mccabe]` |
| Mypy | `pyproject.toml` | `[tool.mypy]`, `[[tool.mypy.overrides]]` |
| Pytest | `pyproject.toml` | `[tool.pytest.ini_options]` |
| Mutmut | `pyproject.toml` | `[tool.mutmut]` |

---

## Dependencias

- Python 3.12 en venv (`./venv/bin/python`)
- Paquetes instalados: `ruff`, `mypy`, `bandit`, `vulture`, `pytest`, `pytest-asyncio`, `pytest-bdd`, `pytest-cov`, `mutmut`
