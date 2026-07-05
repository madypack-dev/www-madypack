"""Tests de integración para las páginas de detalle de producto y el sitemap extendido."""

import pytest
from fastapi.testclient import TestClient

from src.infraestructura.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestProductosEndpoints:
    def test_get_producto_existente_retorna_200_con_schema(self, client):
        response = client.get("/tienda/producto-a-personalizado/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        
        # Verificar que se renderiza la información del producto
        assert "Producto A Personalizado" in response.text
        assert "Descripción del producto A" in response.text
        
        # Verificar que contiene las breadcrumbs
        assert "Inicio" in response.text
        assert "Tienda" in response.text
        
        # Verificar marcado estructurado de tipo Product
        assert 'application/ld+json' in response.text
        assert '"@type": "Product"' in response.text
        assert '"name": "Producto A Personalizado"' in response.text
        assert '"priceCurrency": "ARS"' in response.text

    def test_get_producto_inexistente_retorna_404(self, client):
        response = client.get("/tienda/producto-inexistente/", headers={"host": "localhost:8000"})
        assert response.status_code == 404

    def test_sitemap_xml_incluye_urls_de_productos(self, client):
        response = client.get("/sitemap.xml", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        
        # Debe contener las URLs dinámicas de los productos de la base de datos YAML
        assert "<loc>http://localhost:8000/tienda/producto-a-personalizado/</loc>" in response.text
        assert "<loc>http://localhost:8000/tienda/producto-b-estandar/</loc>" in response.text
        assert "<loc>http://localhost:8000/tienda/producto-c-basico/</loc>" in response.text

    def test_search_productos_returns_filtered_results_with_noindex(self, client):
        # Búsqueda con coincidencia
        response = client.get("/tienda/?q=Personalizado", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Producto A Personalizado" in response.text
        assert "Producto B Estándar" not in response.text

        # Debe incluir la directiva noindex, nofollow para SEO
        assert '<meta name="robots" content="noindex, nofollow">' in response.text

        # El canonical URL debe seguir apuntando a la tienda limpia sin parámetros de query
        assert '<link rel="canonical" href="https://www.tuempresa.com/tienda/">' in response.text

    def test_search_productos_no_query_does_not_contain_noindex(self, client):
        # Búsqueda vacía / sin parámetro de query
        response = client.get("/tienda/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Producto A Personalizado" in response.text
        assert "Producto B Estándar" in response.text

        # NO debe incluir noindex, nofollow sino indexar por defecto
        assert '<meta name="robots" content="noindex, nofollow">' not in response.text

    def test_search_productos_sin_resultados_muestra_mensaje(self, client):
        # Búsqueda que no coincide con nada
        response = client.get("/tienda/?q=inexistente_total_query", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "No se encontraron productos que coincidan con la búsqueda" in response.text
        assert '<meta name="robots" content="noindex, nofollow">' in response.text
