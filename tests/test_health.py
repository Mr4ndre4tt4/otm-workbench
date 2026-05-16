def test_health_returns_application_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "otm-workbench",
        "database": "ok",
    }
