def test_incidents_and_events_are_isolated_between_organizations(client, sample_event):
    created = client.post("/api/v1/events", json=sample_event)
    assert created.status_code == 201
    original_incident_id = created.json()["incident"]["id"]
    second_registration = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Another Workspace",
            "full_name": "Another Owner",
            "email": "another@example.com",
            "password": "another-strong-password-456",
        },
    )
    assert second_registration.status_code == 201
    client.headers.update({"Authorization": f"Bearer {second_registration.json()['access_token']}"})
    assert client.get("/api/v1/incidents").json()["total"] == 0
    assert client.get("/api/v1/events").json() == []
    assert client.get(f"/api/v1/incidents/{original_incident_id}").status_code == 404
