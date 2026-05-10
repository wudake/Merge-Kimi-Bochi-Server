from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "Facebook Video Script Extractor API"
        assert response.json()["version"] == "1.0.0"
        assert response.json()["docs"] == "/docs"
