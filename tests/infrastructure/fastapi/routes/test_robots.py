"""Tests de integración para el endpoint /robots.txt."""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestRobotsTxt:
    def test_robots_txt_genera_sitemap_del_host(self, client):
        response = client.get("/robots.txt", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "User-agent: *" in response.text
        assert "Allow: /" in response.text
        assert "Disallow: /cart/" in response.text
        assert "Disallow: /presupuesto/" in response.text
        assert "Disallow: /presupuesto/descargar/" in response.text
        assert "Sitemap: http://localhost:8000/sitemap.xml" in response.text

    def test_robots_txt_respeta_x_forwarded_proto(self, client):
        response = client.get(
            "/robots.txt",
            headers={
                "host": "www.ejemplo.com",
                "x-forwarded-proto": "https",
            },
        )
        assert response.status_code == 200
        assert "Sitemap: https://www.ejemplo.com/sitemap.xml" in response.text
