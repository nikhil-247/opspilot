def test_registration_returns_owner_token_and_profile(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["role"] == "owner"
    assert response.json()["organization_slug"].startswith("opspilot-test-workspace-")


def test_protected_endpoints_reject_missing_token(client):
    client.headers.pop("Authorization")
    response = client.get("/api/v1/incidents")
    assert response.status_code == 401


def test_login_rejects_incorrect_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.test", "password": "incorrect-password"},
    )
    assert response.status_code == 401


def test_role_permissions_block_viewer_writes(client, sample_event):
    members = client.get("/api/v1/auth/members")
    assert members.status_code == 200
    owner = members.json()[0]
    client.patch(
        f"/api/v1/auth/members/{owner['user_id']}/role",
        json={"role": "viewer"},
    )
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 403
