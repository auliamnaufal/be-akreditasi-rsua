from fastapi.testclient import TestClient

from src.app.models.incident import IncidentStatus


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_perawat_submit_triggers_prediction(client: TestClient, session, perawat_user):
    headers = auth_headers(client, perawat_user.email, "Password123")
    create_resp = client.post(
        "/v1/incidents",
        json={
            "free_text_description": "Pasien hampir jatuh di kamar mandi",
            "attachments": [],
        },
        headers=headers,
    )
    incident_id = create_resp.json()["data"]["id"]

    submit_resp = client.post(f"/v1/incidents/{incident_id}/submit", json={"confirm_submit": True}, headers=headers)
    assert submit_resp.status_code == 200
    data = submit_resp.json()["data"]
    assert data["status"] == IncidentStatus.SUBMITTED.value
    assert data["predicted_category"] is not None
    assert data["predicted_confidence"] is not None


def test_mutu_cannot_review_before_pj(client: TestClient, session, perawat_user, pj_user, mutu_user):
    perawat_headers = auth_headers(client, perawat_user.email, "Password123")
    incident_id = client.post(
        "/v1/incidents",
        json={
            "free_text_description": "Kesalahan obat minor",
        },
        headers=perawat_headers,
    ).json()["data"]["id"]
    client.post(f"/v1/incidents/{incident_id}/submit", json={"confirm_submit": True}, headers=perawat_headers)

    mutu_headers = auth_headers(client, mutu_user.email, "Password123")
    mutu_resp = client.post(
        f"/v1/approvals/{incident_id}/mutu",
        json={"category": "KTD", "notes": "N/A"},
        headers=mutu_headers,
    )
    assert mutu_resp.status_code == 409

    pj_headers = auth_headers(client, pj_user.email, "Password123")
    pj_resp = client.post(
        f"/v1/approvals/{incident_id}/pj",
        json={"category": "KTD", "notes": "Serious"},
        headers=pj_headers,
    )
    assert pj_resp.status_code == 200

    mutu_resp2 = client.post(
        f"/v1/approvals/{incident_id}/mutu",
        json={"category": "KTD", "notes": "Reviewed"},
        headers=mutu_headers,
    )
    assert mutu_resp2.status_code == 200
