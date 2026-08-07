#!/usr/bin/env python3
"""
Clean Architecture Guard - Verificador estático de reglas de dependencia del Tío Bob.

Este script analiza el AST (Abstract Syntax Tree) de todos los módulos bajo `src/`
y asegura de forma determinista que no existan violaciones de la Regla de Dependencia:
- `src/domain`: No debe importar de `application`, `adapters`, `infrastructure`, ni frameworks web/externos.
- `src/application`: No debe importar de `adapters`, `infrastructure`, ni frameworks web/externos.
- `src/adapters`: No debe importar de `infrastructure` ni de FastAPI directamente.
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
        "rule_description": "El Dominio no debe depender de capas externas ni de frameworks."
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
        "rule_description": "La capa de Aplicación no debe depender de Adaptadores ni Infraestructura ni frameworks web."
    },
    "src/adapters": {
        "forbidden_prefixes": (
            "src.infrastructure",
            "fastapi",
        ),
        "rule_description": "Los Adaptadores no deben depender de la capa de Infraestructura."
    },
}


def check_file(file_path: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        return [f"{file_path}: Error de parseo AST: {exc}"]

    for node in ast.walk(tree):
        imported_module = None
        lineno = getattr(node, "lineno", 0)

        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_module = alias.name
                for prefix in forbidden_prefixes:
                    if imported_module == prefix or imported_module.startswith(prefix + "."):
                        violations.append(
                            f"  ⛔ [{file_path.relative_to(Path.cwd())}:{lineno}] "
                            f"Importa '{imported_module}' (violación de prefijo prohibido '{prefix}')"
                        )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_module = node.module
                # Considerar imports relativos dentro del mismo paquete
                if node.level > 0:
                    # Resolve relative import if needed
                    pass
                for prefix in forbidden_prefixes:
                    if imported_module == prefix or imported_module.startswith(prefix + "."):
                        violations.append(
                            f"  ⛔ [{file_path.relative_to(Path.cwd())}:{lineno}] "
                            f"from {imported_module} import ... (violación de prefijo prohibido '{prefix}')"
                        )

    return violations


def main() -> int:
    root_dir = Path.cwd()
    total_violations = 0

    print("🛡️  [CLEAN ARCHITECTURE GUARD] Verificando Reglas de Dependencia del Tío Bob...\n")

    for layer_rel_path, config in FORBIDDEN_IMPORTS.items():
        layer_dir = root_dir / layer_rel_path
        if not layer_dir.exists():
            continue

        forbidden_prefixes = config["forbidden_prefixes"]
        description = config["rule_description"]

        print(f"🔍 Evaluando: {layer_rel_path}/ -> {description}")
        layer_violations = []

        for py_file in layer_dir.rglob("*.py"):
            if py_file.name == "__init__.py" and py_file.stat().st_size == 0:
                continue
            file_violations = check_file(py_file, forbidden_prefixes)
            layer_violations.extend(file_violations)

        if layer_violations:
            print(f"❌ VIOLACIONES DETECTADAS EN {layer_rel_path}:")
            for v in layer_violations:
                print(v)
            total_violations += len(layer_violations)
        else:
            print(f"✅ {layer_rel_path}: Sin violaciones de arquitectura.")
        print()

    if total_violations > 0:
        print(f"💥 GUARDIA FALLIDO: Se encontraron {total_violations} violaciones de Arquitectura Limpia.")
        return 1

    print("👑 GUARDIA EXITOSO: La arquitectura cumple al 100% las reglas de independencia del Tío Bob.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
