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
        json={"email": "owner@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401


def test_role_permissions_block_viewer_writes(client, sample_event):
    workspace = client.get("/api/v1/auth/me").json()
    second_registration = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Temporary Workspace",
            "full_name": "Second User",
            "email": "second@example.com",
            "password": "another-strong-password-123",
        },
    )
    assert second_registration.status_code == 201
    second_user_id = second_registration.json()["user"]["id"]
    added = client.post(
        "/api/v1/auth/members",
        json={"user_id": second_user_id, "role": "viewer"},
    )
    assert added.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "second@example.com",
            "password": "another-strong-password-123",
            "organization_slug": workspace["organization_slug"],
        },
    )
    assert login.status_code == 200
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    member_list = client.get("/api/v1/auth/members")
    assert member_list.status_code == 200
    assert len(member_list.json()) == 2

    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 403
