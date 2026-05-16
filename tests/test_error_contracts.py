def test_404_uses_standard_error_shape(client):
    response = client.get("/missing-route")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["message"]


def test_unauthenticated_uses_standard_error_shape(client):
    response = client.get("/api/v1/platform/workspaces")

    assert response.status_code == 401
    assert response.json() == {
        "code": "UNAUTHENTICATED",
        "message": "A bearer token is required.",
        "details": {},
    }
