import httpx
import pytest

from src.adapters.gateways.xubio_client import XubioErpGateway
from src.domain.erp.entities import EmpresaERP, EstadoConexionERP
from src.infrastructure.config import settings
from src.infrastructure.httpx.http_client import HttpxClientAdapter


@pytest.mark.asyncio
async def test_xubio_gateway_mock_token_y_miempresa():
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "/TokenEndpoint" in url_str:
            assert request.headers.get("Authorization", "").startswith("Basic ")
            return httpx.Response(200, json={"access_token": "token_prueba_123"})
        elif "/miempresa" in url_str:
            assert request.headers.get("Authorization") == "Bearer token_prueba_123"
            return httpx.Response(
                200,
                json={
                    "id": 99,
                    "nombre": "Empresa Pruebas SA",
                    "cuit": "30-11223344-5",
                    "email": "info@pruebas.com",
                },
            )
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=mock_transport) as client:
        http_adapter = HttpxClientAdapter(client)
        gateway = XubioErpGateway(
            client=http_adapter,
            client_id="test_client",
            secret_id="test_secret",
            base_url="https://xubio.com/API/1.1",
        )

        empresa = await gateway.obtener_datos_empresa()

        assert isinstance(empresa, EmpresaERP)
        assert empresa.id == "99"
        assert empresa.nombre == "Empresa Pruebas SA"
        assert empresa.identificacion_tributaria == "30-11223344-5"


@pytest.mark.asyncio
async def test_xubio_gateway_mock_error_token():
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    mock_transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=mock_transport) as client:
        http_adapter = HttpxClientAdapter(client)
        gateway = XubioErpGateway(
            client=http_adapter,
            client_id="bad_client",
            secret_id="bad_secret",
            base_url="https://xubio.com/API/1.1",
        )

        estado = await gateway.verificar_conexion()

        assert isinstance(estado, EstadoConexionERP)
        assert estado.activo is False
        assert "Fallo" in estado.mensaje


@pytest.mark.asyncio
async def test_xubio_conexion_real_produccion():
    """Test de integración real contra Xubio utilizando las credenciales cargadas en .env.

    Realiza GET /miempresa de forma segura (operación de lectura).
    """
    client_id = settings.XUBIO_CLIENT_ID
    secret_id = settings.XUBIO_SECRET_ID

    if not client_id or not secret_id:
        pytest.skip("No hay credenciales de Xubio configuradas en el entorno")

    async with httpx.AsyncClient() as client:
        http_adapter = HttpxClientAdapter(client)
        gateway = XubioErpGateway(client=http_adapter, client_id=client_id, secret_id=secret_id)

        estado = await gateway.verificar_conexion()
        print("\n[Xubio Real Test] Estado de Conexión:", estado)

        assert estado.activo is True, f"Fallo al conectar con Xubio real: {estado.mensaje}"
        assert estado.proveedor == "Xubio"

        empresa = await gateway.obtener_datos_empresa()
        print("[Xubio Real Test] Datos de Empresa obtenidos:", empresa)

        assert empresa.id is not None
        assert len(empresa.nombre) > 0
