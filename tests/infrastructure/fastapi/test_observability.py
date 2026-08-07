from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app import app
from src.infrastructure.fastapi.dependencies import get_http_client_adapter


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
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_client.head.return_value = mock_response

    app.dependency_overrides[get_http_client_adapter] = lambda: mock_client
    try:
        response = client.get("/health", headers={"host": "localhost:8000"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["catalog"] == "ok"
        assert data["services"]["chatwoot"] == "ok"
    finally:
        app.dependency_overrides.clear()
