from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/actuator/health")
    assert response.status_code == 200
    assert response.json() == {"msg": "success"}

