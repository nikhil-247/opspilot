def test_incidents_are_isolated_between_organizations(client, sample_event):
    created = client.post("/api/v1/events", json=sample_event)
    assert created.status_code == 201
    original_incident_id = created.json()["incident"]["id"]

    second_registration = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Another Workspace",
            "full_name": "Another Owner",
            "email": "another@example.test",
            "password": "another-strong-password-456",
        },
    )
    assert second_registration.status_code == 201
    second_token = second_registration.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {second_token}"})

    listing = client.get("/api/v1/incidents")
    assert listing.status_code == 200
    assert listing.json()["total"] == 0
    detail = client.get(f"/api/v1/incidents/{original_incident_id}")
    assert detail.status_code == 404
