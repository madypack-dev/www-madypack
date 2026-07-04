import pytest
from fastapi.testclient import TestClient
from src.infraestructura.app import app

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
