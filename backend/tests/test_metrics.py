def test_prometheus_metrics_endpoint_is_available(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
