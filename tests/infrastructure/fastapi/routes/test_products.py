"""Tests de integración para las páginas de detalle de producto y el sitemap extendido."""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestProductosEndpoints:
    def test_get_producto_visible_retorna_200_con_schema(self, client):
        # Producto visible: compuesto Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g
        response = client.get("/productos/bolsa-de-papel-marron-221030/", headers={"host": "localhost:8000"})
        assert response.status_code == 200

        # Verificar que se renderiza la información del producto
        assert "Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g" in response.text
        assert "Bobina de Papel" in response.text
        assert "Confección de Bolsas de Papel" in response.text

        # Verificar que contiene las breadcrumbs
        assert "Inicio" in response.text
        assert "Productos" in response.text

        # Verificar marcado estructurado de tipo Product
        assert 'application/ld+json' in response.text
        assert '"@type": "Product"' in response.text
        assert '"name":' in response.text

    def test_get_variante_simple_no_visible_retorna_404(self, client):
        response = client.get("/productos/bolsa-de-papel-marron-221030-base/", headers={"host": "localhost:8000"})
        assert response.status_code == 404

    def test_get_servicio_visible_retorna_200(self, client):
        response = client.get("/productos/confeccion-de-bolsas/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Confección de Bolsas de Papel" in response.text

    def test_get_manija_cordon_visible_retorna_200(self, client):
        response = client.get("/productos/manija-cordon/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Manija Cordón" in response.text

    def test_get_pegado_visible_retorna_200(self, client):
        response = client.get("/productos/pegado-de-manijas/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Pegado de Manijas" in response.text

    def test_get_corte_de_bobinas_visible_retorna_200(self, client):
        response = client.get("/productos/corte-de-bobinas/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Corte de Bobinas" in response.text

    def test_get_confeccion_cuerdas_visible_retorna_200(self, client):
        response = client.get(
            "/productos/confeccion-de-cuerdas-de-papel-retorcidas/",
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert "Confección de Cuerdas de Papel Retorcidas" in response.text

    def test_get_compuesto_con_manija_visible_retorna_200(self, client):
        # Solo el compuesto con manija cordón 22x10x30 Marrón es visible
        response = client.get(
            "/productos/bolsa-de-papel-marron-221030-base-con-manija-cordon/",
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert "con Manija Cordón" in response.text

    def test_get_compuesto_impreso_visible_retorna_200(self, client):
        response = client.get(
            "/productos/bolsa-de-papel-impresa-marron-221030-base/",
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert "Impresa" in response.text

    def test_get_compuesto_impreso_con_manija_visible_retorna_200(self, client):
        response = client.get(
            "/productos/bolsa-de-papel-impresa-marron-221030-base-con-manija-cordon/",
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert "Impresa" in response.text
        assert "Manija Cordón" in response.text

    def test_get_cuerdas_de_papel_visible_retorna_200(self, client):
        response = client.get(
            "/productos/cuerdas-de-papel-retorcidas/",
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert "Cuerdas de Papel Retorcidas" in response.text

    def test_sitemap_xml_incluye_urls_de_productos_visibles(self, client):
        response = client.get("/sitemap.xml", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]

        # Debe contener URLs de productos/servicios visibles
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-marron-221030/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/bobina-de-papel/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/confeccion-de-bolsas/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/manija-cordon/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/pegado-de-manijas/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/corte-de-bobinas/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/confeccion-de-cuerdas-de-papel-retorcidas/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-marron-221030-base-con-manija-cordon/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-impresa-marron-221030-base/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-impresa-marron-221030-base-con-manija-cordon/</loc>" in response.text
        assert "<loc>http://localhost:8000/productos/cuerdas-de-papel-retorcidas/</loc>" in response.text
        # No debe contener productos no visibles
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-blanco-221030/</loc>" not in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-marron-120819-con-manija-cordon/</loc>" not in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-impresa-marron-120819/</loc>" not in response.text
        assert "<loc>http://localhost:8000/productos/bolsa-de-papel-impresa-marron-120819-con-manija-cordon/</loc>" not in response.text

    def test_search_productos_returns_filtered_results_with_noindex(self, client):
        # Búsqueda con coincidencia en producto/servicio visible
        response = client.get("/productos/?q=Bobina", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Bobina de Papel" in response.text

        # Debe incluir la directiva noindex, nofollow para SEO
        assert '<meta name="robots" content="noindex, nofollow">' in response.text

        # El canonical URL debe seguir apuntando a la tienda limpia sin parámetros de query
        assert '<link rel="canonical" href="https://www.madypack.com.ar/productos/">' in response.text

    def test_search_productos_no_query_does_not_contain_noindex(self, client):
        # Búsqueda vacía / sin parámetro de query
        response = client.get("/productos/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Bolsa" in response.text

        # NO debe incluir noindex, nofollow sino indexar por defecto
        assert '<meta name="robots" content="noindex, nofollow">' not in response.text

    def test_search_productos_sin_resultados_muestra_mensaje(self, client):
        # Búsqueda que no coincide con nada
        response = client.get("/productos/?q=inexistente_total_query", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "No se encontraron productos que coincidan con la búsqueda" in response.text
        assert '<meta name="robots" content="noindex, nofollow">' in response.text
