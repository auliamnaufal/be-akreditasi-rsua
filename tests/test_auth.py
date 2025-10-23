from fastapi.testclient import TestClient

from src.app.schemas.auth import LoginRequest


def test_login_and_refresh(client: TestClient, session, perawat_user):
    response = client.post(
        "/v1/auth/login",
        json={"email": perawat_user.email, "password": "Password123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    refresh_token = data["refresh_token"]

    refresh_response = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()["data"]
    assert refreshed["access_token"] != data["access_token"]
