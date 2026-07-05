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
