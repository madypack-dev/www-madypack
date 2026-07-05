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

def test_tenant_css_bundle_isolation(client):
    # 1. Solicitar bundle con host por defecto (eitec)
    response_default = client.get("/static/css/bundle.css", headers={"host": "localhost:8000"})
    assert response_default.status_code == 200
    assert "--primary: #2853A1;" in response_default.text

    # 2. Solicitar bundle con host de madypack
    response_madypack = client.get("/static/css/bundle.css", headers={"host": "madypack.com.ar"})
    assert response_madypack.status_code == 200
    assert "--primary: #c12a2a;" in response_madypack.text
    assert "--primary-dark: #8f1f1f;" in response_madypack.text

def test_structlog_json_rendering_and_context_vars(monkeypatch, caplog):
    import json
    import logging
    import structlog
    from src.infraestructura.logging.logger import configurar_logging, get_logger

    # Forzar formato JSON usando variable de entorno
    monkeypatch.setenv("LOG_FORMAT", "json")
    configurar_logging()

    logger_test = get_logger("test-json")

    # Bind variables de contexto de structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="test-req-123", tenant="test-tenant")

    with caplog.at_level(logging.INFO):
        logger_test.info("Mensaje de prueba", extra_field="value")

    assert caplog.text != ""
    # El logger puede tener otros prefijos dependientes del test run, extraemos el json del cuerpo
    line = caplog.text.strip().splitlines()[-1]
    # Si pytest le mete el prefijo del nivel (ej: "INFO     test-json:test_observabilidad.py:82 "), lo limpiamos
    if " {" in line:
        line = "{" + line.split(" {", 1)[1]
    
    log_data = json.loads(line)

    assert log_data["event"] == "Mensaje de prueba"
    assert log_data["request_id"] == "test-req-123"
    assert log_data["tenant"] == "test-tenant"
    assert log_data["extra_field"] == "value"
    assert log_data["level"] == "info"
    assert "timestamp" in log_data

    # Restaurar formateador por defecto para no interferir con otros tests
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    configurar_logging()
