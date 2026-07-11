"""Tests de integración para el middleware global de normalización de trailing slash (301)."""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.app import app


@pytest.fixture
def client():
    # Desactivar follow_redirects para comprobar los códigos de estado 301
    return TestClient(app, follow_redirects=False)


class TestTrailingSlashMiddleware:
    def test_redirects_without_trailing_slash_to_trailing_slash(self, client):
        response = client.get("/productos", headers={"host": "localhost:8000"})
        assert response.status_code == 301
        assert response.headers["location"] == "/productos/"

    def test_does_not_redirect_if_already_has_trailing_slash(self, client):
        response = client.get("/productos/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_redirects_inner_pages_without_trailing_slash(self, client):
        response = client.get("/quienes-somos", headers={"host": "localhost:8000"})
        assert response.status_code == 301
        assert response.headers["location"] == "/quienes-somos/"

    def test_preserves_query_parameters_on_redirect(self, client):
        response = client.get("/productos?success=1&cat=industrial", headers={"host": "localhost:8000"})
        assert response.status_code == 301
        assert response.headers["location"] == "/productos/?success=1&cat=industrial"

    def test_does_not_redirect_root_path(self, client):
        response = client.get("/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_does_not_redirect_excluded_routes(self, client):
        # /health
        response_health = client.get("/health", headers={"host": "localhost:8000"})
        assert response_health.status_code == 200

        # /robots.txt
        response_robots = client.get("/robots.txt", headers={"host": "localhost:8000"})
        assert response_robots.status_code == 200

        # /sitemap.xml
        response_sitemap = client.get("/sitemap.xml", headers={"host": "localhost:8000"})
        assert response_sitemap.status_code == 200

    def test_does_not_redirect_static_files(self, client):
        # Intentamos obtener un archivo estático CSS
        response = client.get("/static/css/layout.css", headers={"host": "localhost:8000"})
        assert response.status_code == 200

    def test_does_not_redirect_files_with_extension(self, client):
        # Cualquier ruta que parezca un archivo (tenga un punto en la última parte del path) no debe redirigirse a /
        response = client.get("/favicon.ico", headers={"host": "localhost:8000"})
        # Retorna 404 porque el archivo no existe, pero no debería redirigir con 301
        assert response.status_code == 404
