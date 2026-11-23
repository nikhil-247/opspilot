def test_incident_analysis_returns_evidence_and_limitations(client, sample_event):
    created = client.post("/api/v1/events", json=sample_event).json()
    analysis = client.get(f"/api/v1/incidents/{created['incident']['id']}/analysis")
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["incident_id"] == created["incident"]["id"]
    assert body["summary"].startswith("Reviewed 1 events")
    assert isinstance(body["hypotheses"], list)
    assert body["limitations"]
