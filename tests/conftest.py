import pytest

@pytest.fixture(autouse=True, scope="session")
def setup_css_bundle():
    """Compila los bundles de CSS antes de ejecutar las pruebas para que estén disponibles en el sistema de archivos."""
    from src.infraestructura.build.css_bundle import compilar_bundle_css
    compilar_bundle_css()
