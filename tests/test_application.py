from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_discover_canada():
    response = client.post("/api/discover", json={"country": "Canada"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["country"] == "Canada"
    assert payload["status"] == "completed"
    assert payload["university_count"] > 0
    assert len(payload["universities"]) > 0


def test_invalid_country():
    response = client.post("/api/discover", json={"country": "NotARealPlace"})
    assert response.status_code == 400


def test_list_universities():
    response = client.get("/api/universities", params={"country": "Canada"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["name"] == "University of Toronto" for item in data)
