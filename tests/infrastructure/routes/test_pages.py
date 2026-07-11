import pytest
from fastapi.testclient import TestClient
from src.infrastructure.app import app

@pytest.fixture
def client():
    return TestClient(app)

class TestPaginasEndpoints:
    def test_get_root(self, client):
        response = client.get("/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_post_root_newsletter(self, client):
        response = client.post(
            "/",
            data={"email": "newsletter@example.com"},
            headers={"host": "localhost:8000"},
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/?success=newsletter"

    def test_post_root_quote(self, client):
        response = client.post(
            "/",
            data={"phone": "123456789", "email": "quote@example.com"},
            headers={"host": "localhost:8000"},
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/?success=quote"

    def test_get_quienes_somos(self, client):
        response = client.get("/quienes-somos/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_get_contacto(self, client):
        response = client.get("/contacto/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_get_terminos_y_condiciones(self, client):
        response = client.get("/terminos-y-condiciones/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_get_politica_de_privacidad(self, client):
        response = client.get("/politica-de-privacidad/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_get_productos_renders_schema(self, client):
        response = client.get("/productos/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        # Verificar contenido general
        assert "Catálogo de" in response.text
        # Verificar marcado estructurado JSON-LD
        assert 'application/ld+json' in response.text
        assert '"@type": "ItemList"' in response.text
        assert '"@type": "Product"' in response.text
        assert '"name":' in response.text
        assert '"image":' in response.text

    def test_get_tienda_redirects_to_productos(self, client):
        response = client.get("/tienda/", headers={"host": "localhost:8000"}, follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "/productos/"

    def test_post_contacto_success(self, client):
        response = client.post(
            "/contacto/",
            data={
                "wpforms[fields][0]": "Juan Pérez",
                "wpforms[fields][4]": "+5491112345678",
                "wpforms[fields][1]": "juan@example.com",
                "wpforms[fields][2]": "Hola, necesito más información sobre los envíos a Mendoza.",
            },
            headers={"host": "localhost:8000"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/contacto/?success=contacto"

    def test_post_contacto_missing_data(self, client):
        response = client.post(
            "/contacto/",
            data={
                "wpforms[fields][0]": "Juan Pérez",
                # Falta teléfono, email y mensaje
            },
            headers={"host": "localhost:8000"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/contacto/?error=datos_invalidos"
