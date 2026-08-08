from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from scripts.check_clean_architecture import FORBIDDEN_IMPORTS, check_file

scenarios("clean_architecture.feature")


@given(parsers.parse('la estructura actual del paquete "{paquete}"'), target_fixture="domain_path")
def domain_path(paquete: str) -> Path:
    path = Path.cwd() / paquete
    assert path.exists(), f"El paquete {paquete} no existe"
    return path


@when("ejecuto la inspección sintáctica de dependencias", target_fixture="violations")
def inspect_dependencies(domain_path: Path) -> list[str]:
    forbidden_prefixes = FORBIDDEN_IMPORTS["src/domain"]["forbidden_prefixes"]
    violations = []
    for py_file in domain_path.rglob("*.py"):
        if py_file.name == "__init__.py" and py_file.stat().st_size == 0:
            continue
        file_violations = check_file(py_file, forbidden_prefixes)
        violations.extend(file_violations)
    return violations


@then(
    parsers.parse(
        'no debe detectarse ninguna importación proveniente de "{item1}", "{item2}" ni "{item3}"'
    )
)
def verify_no_forbidden_imports(violations: list[str], item1: str, item2: str, item3: str) -> None:
    assert len(violations) == 0, f"Se detectaron violaciones en el dominio: {violations}"


def test_no_relative_imports_in_src():
    """Garantiza que no existan importaciones relativas (from .import ...) en src/."""
    src_dir = Path.cwd() / "src"
    relative_import_violations = []
    for py_file in src_dir.rglob("*.py"):
        violations = check_file(py_file, ())
        for v in violations:
            if "Prohibida importación relativa" in v:
                relative_import_violations.append(v)

    assert len(relative_import_violations) == 0, (
        f"Se encontraron importaciones relativas en src/: {relative_import_violations}"
    )


def test_empty_init_py_files_in_src():
    """Garantiza que todos los archivos __init__.py en src/ estén 100% vacíos (0 bytes)."""
    src_dir = Path.cwd() / "src"
    non_empty_inits = []
    for py_file in src_dir.rglob("__init__.py"):
        if py_file.stat().st_size > 0:
            if "_mutmut_" in py_file.read_text(encoding="utf-8"):
                continue
            non_empty_inits.append(str(py_file.relative_to(Path.cwd())))

    assert len(non_empty_inits) == 0, (
        f"Se encontraron archivos __init__.py no vacíos en src/: {non_empty_inits}"
    )
