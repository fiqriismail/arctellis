from fastapi.testclient import TestClient


def test_health_returns_200():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
