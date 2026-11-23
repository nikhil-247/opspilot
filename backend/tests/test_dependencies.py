def test_service_dependencies_are_saved_and_listed(client):
    created = client.post(
        "/api/v1/services/dependencies",
        json={
            "source_service": "checkout-api",
            "target_service": "payment-service",
        },
    )
    assert created.status_code == 201
    listing = client.get("/api/v1/services/dependencies")
    assert listing.status_code == 200
    assert listing.json()[0]["source_service"] == "checkout-api"


def test_service_cannot_depend_on_itself(client):
    response = client.post(
        "/api/v1/services/dependencies",
        json={"source_service": "payments", "target_service": "payments"},
    )
    assert response.status_code == 422
