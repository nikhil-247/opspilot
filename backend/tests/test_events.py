def test_error_event_creates_p2_incident(client, sample_event):
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    body = response.json()
    assert body["event"]["service"] == "payment-service"
    assert body["incident_created"] is True
    assert body["incident"]["priority"] == "P2"
    assert body["incident"]["status"] == "open"
    assert body["incident"]["occurrence_count"] == 1


def test_info_event_is_stored_without_creating_incident(client, sample_event):
    sample_event["severity"] = "info"
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    body = response.json()
    assert body["incident"] is None
    assert body["event"]["incident_id"] is None
    assert body["incident_created"] is False


def test_repeated_events_are_deduplicated_and_counted(client, sample_event):
    first = client.post("/api/v1/events", json=sample_event).json()
    second = client.post("/api/v1/events", json=sample_event).json()
    assert first["incident"]["id"] == second["incident"]["id"]
    assert first["incident_created"] is True
    assert second["incident_created"] is False
    assert second["incident"]["occurrence_count"] == 2
    assert len(client.get("/api/v1/events").json()) == 2


def test_critical_event_escalates_existing_incident(client, sample_event):
    first = client.post("/api/v1/events", json=sample_event).json()
    sample_event["severity"] = "critical"
    second = client.post("/api/v1/events", json=sample_event).json()
    assert first["incident"]["id"] == second["incident"]["id"]
    assert second["incident"]["priority"] == "P1"
    assert second["incident"]["severity"] == "critical"


def test_warning_event_creates_lower_priority_incident(client, sample_event):
    sample_event["severity"] = "warning"
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    assert response.json()["incident"]["priority"] == "P3"


def test_invalid_event_is_rejected(client, sample_event):
    sample_event["severity"] = "urgent"
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 422


def test_fingerprint_normalizes_case_and_whitespace(client, sample_event):
    first = client.post("/api/v1/events", json=sample_event).json()
    sample_event["message"] = "  DATABASE   CONNECTION POOL EXHAUSTED  "
    second = client.post("/api/v1/events", json=sample_event).json()
    assert first["incident"]["id"] == second["incident"]["id"]
    assert second["incident"]["occurrence_count"] == 2


def test_critical_event_reopens_resolved_incident_and_escalates(client, sample_event):
    created = client.post("/api/v1/events", json=sample_event).json()["incident"]
    incident_id = created["id"]

    resolved = client.post(f"/api/v1/incidents/{incident_id}/resolve", json={})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    sample_event["severity"] = "critical"
    reopened = client.post("/api/v1/events", json=sample_event)
    assert reopened.status_code == 201
    incident = reopened.json()["incident"]
    assert incident["id"] == incident_id
    assert incident["priority"] == "P1"
    assert incident["status"] == "open"
    assert incident["resolved_at"] is None

    actions = client.get(f"/api/v1/incidents/{incident_id}/activity").json()
    assert [item["action"] for item in actions] == [
        "created",
        "resolved",
        "escalated",
        "reopened",
    ]


def test_event_explorer_filters_by_service_severity_and_search(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    second_event = {
        **sample_event,
        "service": "catalog-service",
        "event_type": "cache_miss",
        "severity": "warning",
        "message": "Product cache miss",
    }
    client.post("/api/v1/events", json=second_event)

    filtered = client.get(
        "/api/v1/events?service=payment-service&severity=error&search=connection"
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["service"] == "payment-service"

    warning_events = client.get("/api/v1/events?severity=warning")
    assert len(warning_events.json()) == 1
    assert warning_events.json()[0]["event_type"] == "cache_miss"
