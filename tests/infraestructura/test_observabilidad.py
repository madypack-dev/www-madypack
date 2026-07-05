import pytest
from fastapi.testclient import TestClient
from src.infraestructura.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_request_id_middleware(client):
    response = client.get("/robots.txt", headers={"host": "localhost:8000"})
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

def test_chrome_devtools_silent_route(client):
    response = client.get("/.well-known/appspecific/com.chrome.devtools.json", headers={"host": "localhost:8000"})
    assert response.status_code == 200
    assert response.json() == {}

def test_health_check_endpoint(client):
    response = client.get("/health", headers={"host": "localhost:8000"})
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "catalog" in data["services"]
    assert "chatwoot" in data["services"]

def test_global_exception_handler():
    # Instanciamos TestClient con raise_server_exceptions=False para verificar el exception handler de FastAPI
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    
    @app.get("/test-error-500/", include_in_schema=False)
    async def route_error():
        raise RuntimeError("Test simulated crash")

    response = client_no_raise.get("/test-error-500/", headers={"host": "localhost:8000"})
    assert response.status_code == 500
    assert "text/html" in response.headers["content-type"]
    assert "Ha ocurrido un error inesperado" in response.text

def test_response_compression(client):
    # robots.txt tiene menos de 1000 bytes, no debe comprimirse
    response_robots = client.get("/robots.txt", headers={
        "host": "localhost:8000",
        "accept-encoding": "gzip"
    })
    assert response_robots.status_code == 200
    assert "content-encoding" not in response_robots.headers

    # La página de inicio es mayor a 1000 bytes, debe comprimirse
    response_home = client.get("/", headers={
        "host": "localhost:8000",
        "accept-encoding": "gzip"
    })
    assert response_home.status_code == 200
    assert response_home.headers["content-encoding"] == "gzip"
