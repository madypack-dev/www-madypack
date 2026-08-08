import pytest
from fastapi.testclient import TestClient

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.infrastructure.fastapi.app_integracion_erp import app_erp
from src.infrastructure.fastapi.dependencies import get_erp_gateway


@pytest.fixture
def client_erp():
    app_erp.dependency_overrides[get_erp_gateway] = lambda: NullErpGateway()
    yield TestClient(app_erp)
    app_erp.dependency_overrides.clear()


def test_replica_xubio_miempresa_endpoint(client_erp):
    response = client_erp.get("/api/v1/xubio/miempresa")
    assert response.status_code == 200
    data = response.json()
    assert data is not None


def test_replica_xubio_cliente_bean_post_rechazado_read_only(client_erp):
    payload = {"nombre": "Cliente Prueba", "numeroIdentificacion": "20123456789"}
    response = client_erp.post("/api/v1/xubio/clienteBean", json=payload)
    # Debe ser 405 Method Not Allowed ya que la réplica de Xubio es estrictamente SOLO LECTURA (GET)
    assert response.status_code == 405


def test_replica_xubio_presupuesto_bean_post_rechazado_read_only(client_erp):
    payload = {"clienteId": 1, "montoTotal": 15000.0}
    response = client_erp.post("/api/v1/xubio/presupuestoBean", json=payload)
    # Debe ser 405 Method Not Allowed ya que la réplica de Xubio es estrictamente SOLO LECTURA (GET)
    assert response.status_code == 405


def test_replica_xubio_producto_stock_get(client_erp):
    response = client_erp.get("/api/v1/xubio/productoStock?productoId=1")
    assert response.status_code == 200
    data = response.json()
    assert data is not None
