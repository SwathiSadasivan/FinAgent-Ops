from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_empty_payload():
    response = client.post("/analyze", json={"text": ""})
    assert response.status_code == 400