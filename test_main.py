from fastapi.testclient import TestClient
from main import app
client = TestClient(app)


def test_home():
    login_response = client.post(
        "/login",
        data={"username": "admin", "password": "1234"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    response = client.get(
        "/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200