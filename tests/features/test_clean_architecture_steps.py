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


@then(parsers.parse('no debe detectarse ninguna importación proveniente de "{item1}", "{item2}" ni "{item3}"'))
def verify_no_forbidden_imports(violations: list[str], item1: str, item2: str, item3: str) -> None:
    assert len(violations) == 0, f"Se detectaron violaciones en el dominio: {violations}"
