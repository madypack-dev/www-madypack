"""Tests de integración para las rutas de presupuesto."""

import json

import pytest
from fastapi.testclient import TestClient

from src.infraestructura.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestPresupuestoEndpoints:
    def test_get_cotizacion_muestra_formulario(self, client):
        response = client.get("/cotizacion/", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        assert "Pedido de cotización" in response.text

    def test_post_presupuesto_genera_pdf(self, client):
        carrito = [
            {
                "id": 1,
                "nombre": "Bolsas de Papel Kraft Personalizadas",
                "descripcion": "Impresión Flexográfica | Manijas planas",
                "cantidad": 1000,
                "imagen": "bolsas-personalizadas.svg",
                "calculo": {
                    "tipo": "suma_por_unidad_mas_fijo",
                    "conceptos": ["base", "manija_plana", "personalizacion"],
                    "concepto_fijo": "fijo_matriz",
                },
            }
        ]
        response = client.post(
            "/presupuesto/",
            data={
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "phone": "5491112345678",
                "company": "ACME",
                "message": "Necesito presupuesto",
            },
            cookies={"articulos_carrito": json.dumps(carrito)},
            headers={"host": "localhost:8000"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert "presupuesto-tu-empresa.pdf" in response.headers["content-disposition"]

    def test_post_presupuesto_sin_carrito_redirige(self, client):
        response = client.post(
            "/presupuesto/",
            data={
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "phone": "5491112345678",
            },
            headers={"host": "localhost:8000"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/cotizacion/?error=" in response.headers["location"]

    def test_post_presupuesto_datos_invalidos_redirige(self, client):
        carrito = [
            {
                "id": 1,
                "nombre": "Bolsas",
                "descripcion": "Desc",
                "cantidad": 1000,
                "imagen": "bolsas.svg",
                "calculo": {
                    "tipo": "suma_por_unidad",
                    "conceptos": ["base"],
                },
            }
        ]
        response = client.post(
            "/presupuesto/",
            data={
                "name": "Juan Pérez",
                "email": "no-es-email",
                "phone": "5491112345678",
            },
            cookies={"articulos_carrito": json.dumps(carrito)},
            headers={"host": "localhost:8000"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/cotizacion/?error=datos_invalidos" in response.headers["location"]
