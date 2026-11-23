from types import SimpleNamespace


def test_async_event_endpoint_enqueues_event(client, sample_event, monkeypatch):
    captured = {}

    def fake_delay(organization_id, payload):
        captured["organization_id"] = organization_id
        captured["payload"] = payload
        return SimpleNamespace(id="test-task-123")

    monkeypatch.setattr("app.api.routes.events.process_event.delay", fake_delay)
    response = client.post("/api/v1/events/async", json=sample_event)
    assert response.status_code == 202
    assert response.json() == {"task_id": "test-task-123", "status": "queued"}
    assert captured["organization_id"]
    assert captured["payload"]["service"] == "payment-service"
