import pytest
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app_integracion_erp import app_erp
from src.infrastructure.fastapi.app_web_publica import app_web


def test_entrypoint_web_publica_salud():
    client = TestClient(app_web)
    response = client.get("/health", follow_redirects=True)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_entrypoint_integracion_erp_salud():
    client = TestClient(app_erp)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "erp_integracion_privado"


def test_entrypoint_integracion_erp_conexion():
    client = TestClient(app_erp)
    response = client.get("/api/v1/erp/conexion")
    assert response.status_code == 200
    data = response.json()
    assert "activo" in data
    assert "proveedor" in data
