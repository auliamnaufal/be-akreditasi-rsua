from fastapi.testclient import TestClient


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_perawat_cannot_access_admin(client: TestClient, session, perawat_user):
    headers = auth_headers(client, perawat_user.email, "Password123")
    response = client.get("/v1/admin/users", headers=headers)
    assert response.status_code == 403
    body = response.json()
    assert body["error_code"] == "role_not_allowed"


def test_admin_can_manage_users(client: TestClient, session, admin_user):
    headers = auth_headers(client, admin_user.email, "Password123")
    response = client.get("/v1/admin/users", headers=headers)
    assert response.status_code == 200
