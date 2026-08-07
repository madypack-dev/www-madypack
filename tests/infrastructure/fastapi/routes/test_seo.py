from fastapi.testclient import TestClient
from src.infrastructure.fastapi.app import app

client = TestClient(app)

def test_sitemap_xml():
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<urlset" in response.text
    assert "<loc>" in response.text

def test_robots_txt():
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8" or "text/plain" in response.headers["content-type"]
    assert "User-agent: *" in response.text
    assert "Sitemap:" in response.text
