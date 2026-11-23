def _create_incident(client, sample_event):
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    return response.json()["incident"]


def test_incident_can_be_acknowledged_and_resolved(client, sample_event):
    incident = _create_incident(client, sample_event)
    incident_id = incident["id"]

    acknowledged = client.post(
        f"/api/v1/incidents/{incident_id}/acknowledge",
        json={"actor": "nikhil", "note": "Investigating database pool"},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_at"] is not None

    resolved = client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={"actor": "nikhil", "note": "Connection pool recovered"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None


def test_invalid_status_transition_returns_conflict(client, sample_event):
    incident = _create_incident(client, sample_event)
    incident_id = incident["id"]
    first = client.post(f"/api/v1/incidents/{incident_id}/acknowledge", json={})
    second = client.post(f"/api/v1/incidents/{incident_id}/acknowledge", json={})
    assert first.status_code == 200
    assert second.status_code == 409


def test_resolved_incident_reopens_when_matching_event_arrives(client, sample_event):
    incident = _create_incident(client, sample_event)
    incident_id = incident["id"]
    resolved = client.post(f"/api/v1/incidents/{incident_id}/resolve", json={})
    assert resolved.json()["status"] == "resolved"

    repeated = client.post("/api/v1/events", json=sample_event)
    assert repeated.status_code == 201
    assert repeated.json()["incident"]["status"] == "open"


def test_incident_activity_is_audited(client, sample_event):
    incident = _create_incident(client, sample_event)
    incident_id = incident["id"]
    client.post(f"/api/v1/incidents/{incident_id}/acknowledge", json={"actor": "on-call"})
    client.post(f"/api/v1/incidents/{incident_id}/resolve", json={"actor": "on-call"})
    activity = client.get(f"/api/v1/incidents/{incident_id}/activity")
    assert activity.status_code == 200
    assert [item["action"] for item in activity.json()] == ["created", "acknowledged", "resolved"]


def test_incident_list_filters_and_paginates(client, sample_event):
    _create_incident(client, sample_event)
    response = client.get("/api/v1/incidents?status=open&priority=P2&limit=10&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["service"] == "payment-service"


def test_missing_incident_returns_404(client):
    response = client.get("/api/v1/incidents/not-a-real-id")
    assert response.status_code == 404


def test_critical_incident_has_shorter_response_target(client, sample_event):
    sample_event["severity"] = "critical"
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    incident = response.json()["incident"]
    from datetime import datetime

    created = datetime.fromisoformat(incident["created_at"].replace("Z", "+00:00"))
    due = datetime.fromisoformat(incident["sla_due_at"].replace("Z", "+00:00"))
    assert 0 < (due - created).total_seconds() <= 15 * 60
