"""Tests de integración para las páginas de detalle de producto y el sitemap extendido."""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestProductosEndpoints:
    def test_get_producto_existente_retorna_200_con_schema(self, client):
        response = client.get("/productos/bolsa-de-papel/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

        # Verificar que se renderiza la información del producto
        assert "Bolsa de Papel" in response.text
        assert "B-SOS-M" in response.text

        # Verificar que contiene las breadcrumbs
        assert "Inicio" in response.text
        assert "Productos" in response.text

        # Verificar marcado estructurado de tipo Product
        assert 'application/ld+json' in response.text
        assert '"@type": "Product"' in response.text
        assert '"name": "Bolsa de Papel"' in response.text

    def test_get_producto_inexistente_retorna_404(self, client):
        response = client.get("/productos/producto-inexistente/", headers={"host": "localhost:8000"})
        assert response.status_code == 404

    def test_sitemap_xml_incluye_urls_de_productos(self, client):
        response = client.get("/sitemap.xml", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]

        # Debe contener las URLs dinámicas de los productos de la base de datos
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel/</loc>" in response.text

    def test_search_productos_returns_filtered_results_with_noindex(self, client):
        # Búsqueda con coincidencia
        response = client.get("/productos/?q=Papel", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Bolsa de Papel" in response.text

        # Debe incluir la directiva noindex, nofollow para SEO
        assert '<meta name="robots" content="noindex, nofollow">' in response.text

        # El canonical URL debe seguir apuntando a la tienda limpia sin parámetros de query
        assert '<link rel="canonical" href="https://www.madypack.com.ar/productos/">' in response.text

    def test_search_productos_no_query_does_not_contain_noindex(self, client):
        # Búsqueda vacía / sin parámetro de query
        response = client.get("/productos/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Bolsa de Papel" in response.text

        # NO debe incluir noindex, nofollow sino indexar por defecto
        assert '<meta name="robots" content="noindex, nofollow">' not in response.text

    def test_search_productos_sin_resultados_muestra_mensaje(self, client):
        # Búsqueda que no coincide con nada
        response = client.get("/productos/?q=inexistente_total_query", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "No se encontraron productos que coincidan con la búsqueda" in response.text
        assert '<meta name="robots" content="noindex, nofollow">' in response.text
