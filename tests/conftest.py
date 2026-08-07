import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_en_mutants = os.path.basename(root_dir) == "mutants"
if _en_mutants:
    root_dir = os.path.abspath(os.path.join(root_dir, ".."))

if root_dir not in sys.path:
    if _en_mutants:
        # En modo mutmut, insertar la raíz real DESPUÉS de mutants/src/
        # para que el código mutado tenga prioridad sobre el original.
        sys.path.append(root_dir)
    else:
        sys.path.insert(0, root_dir)

try:
    import src

    real_src_dir = os.path.join(root_dir, "src")
    if hasattr(src, "__path__") and real_src_dir not in src.__path__:
        src.__path__.append(real_src_dir)
except ImportError:
    pass

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def setup_css_bundle():
    """Compila los bundles de CSS antes de ejecutar las pruebas para que estén disponibles en el sistema de archivos."""
    from src.infrastructure.tailwindcss.css_bundle import compilar_bundle_css

    compilar_bundle_css()
