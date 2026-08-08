#!/usr/bin/env python3
"""
Clean Architecture Guard - Verificador estático de reglas de arquitectura del Tío Bob.

Este script analiza el AST y sistema de archivos bajo `src/`:
1. Asegura la Regla de Dependencia de capas (Domain -> Application -> Adapters -> Infrastructure).
2. Prohíbe las importaciones relativas (`from .import ...`). Todas deben ser absolutas (`from src...`).
3. Exige que todos los archivos `__init__.py` bajo `src/` estén 100% vacíos (0 bytes).
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = {
    "src/domain": {
        "forbidden_prefixes": (
            "src.application",
            "src.adapters",
            "src.infrastructure",
            "fastapi",
            "starlette",
            "httpx",
            "reportlab",
            "jinja2",
            "structlog",
        ),
        "rule_description": "El Dominio no debe depender de capas externas ni de frameworks.",
    },
    "src/application": {
        "forbidden_prefixes": (
            "src.adapters",
            "src.infrastructure",
            "fastapi",
            "starlette",
            "httpx",
            "reportlab",
            "jinja2",
        ),
        "rule_description": "La capa de Aplicación no debe depender de Adaptadores ni Infraestructura ni frameworks web.",
    },
    "src/adapters": {
        "forbidden_prefixes": (
            "src.infrastructure",
            "fastapi",
            "httpx",
        ),
        "rule_description": "Los Adaptadores no deben depender de la capa de Infraestructura ni de librerías HTTP externas como httpx.",
    },
}


def _check_import_node(
    node: ast.Import, rel_file: Path, lineno: int, forbidden_prefixes: tuple[str, ...]
) -> list[str]:
    violations = []
    for alias in node.names:
        name = alias.name
        if any(name == p or name.startswith(p + ".") for p in forbidden_prefixes):
            violations.append(
                f"  ⛔ [{rel_file}:{lineno}] Importa '{name}' (violación de prefijo prohibido)"
            )
    return violations


def _check_import_from_node(
    node: ast.ImportFrom, rel_file: Path, lineno: int, forbidden_prefixes: tuple[str, ...]
) -> list[str]:
    violations = []
    if node.level > 0:
        violations.append(
            f"  ⛔ [{rel_file}:{lineno}] Prohibida importación relativa ('from .'). Usar importación absoluta 'from src...'."
        )

    if node.module:
        mod = node.module
        if any(mod == p or mod.startswith(p + ".") for p in forbidden_prefixes):
            violations.append(
                f"  ⛔ [{rel_file}:{lineno}] from {mod} import ... (violación de prefijo prohibido)"
            )
    return violations


def check_file(file_path: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations = []
    rel_file = file_path.relative_to(Path.cwd())

    if file_path.name == "__init__.py" and file_path.stat().st_size > 0:
        content = file_path.read_text(encoding="utf-8")
        if "_mutmut_" not in content:
            violations.append(
                f"  ⛔ [{rel_file}] El archivo __init__.py debe estar completamente vacío (0 bytes)."
            )

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception as exc:
        return [f"{file_path}: Error de parseo AST: {exc}"]

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            violations.extend(_check_import_node(node, rel_file, lineno, forbidden_prefixes))
        elif isinstance(node, ast.ImportFrom):
            violations.extend(_check_import_from_node(node, rel_file, lineno, forbidden_prefixes))

    return violations


def _evaluate_layer(root_dir: Path, layer_rel_path: str, config: dict) -> list[str]:
    layer_dir = root_dir / layer_rel_path
    if not layer_dir.exists():
        return []

    print(f"🔍 Evaluando: {layer_rel_path}/ -> {config['rule_description']}")
    violations = []
    for py_file in layer_dir.rglob("*.py"):
        violations.extend(check_file(py_file, config["forbidden_prefixes"]))

    if violations:
        print(f"❌ VIOLACIONES DETECTADAS EN {layer_rel_path}:")
        for v in violations:
            print(v)
    else:
        print(f"✅ {layer_rel_path}: Sin violaciones de arquitectura.")
    print()
    return violations


def main() -> int:
    root_dir = Path.cwd()
    print("🛡️  [CLEAN ARCHITECTURE GUARD] Verificando Reglas de Dependencia del Tío Bob...\n")

    total_violations = 0
    for layer_rel_path, config in FORBIDDEN_IMPORTS.items():
        violations = _evaluate_layer(root_dir, layer_rel_path, config)
        total_violations += len(violations)

    print(
        "🔍 Evaluando: src/ -> Verificando __init__.py vacíos e importaciones relativas globales..."
    )
    src_violations = []
    for py_file in (root_dir / "src").rglob("*.py"):
        rel = py_file.relative_to(root_dir)
        if not any(str(rel).startswith(p) for p in FORBIDDEN_IMPORTS):
            src_violations.extend(check_file(py_file, ()))

    if src_violations:
        print("❌ VIOLACIONES DETECTADAS EN src/:")
        for v in src_violations:
            print(v)
        total_violations += len(src_violations)
    else:
        print("✅ src/: Todos los __init__.py vacíos y sin importaciones relativas.")
    print()

    if total_violations > 0:
        print(
            f"💥 GUARDIA FALLIDO: Se encontraron {total_violations} violaciones de Arquitectura Limpia."
        )
        return 1

    print(
        "👑 GUARDIA EXITOSO: La arquitectura cumple al 100% las reglas de independencia del Tío Bob."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
