def test_current_user_requires_session(client):
    response = client.get("/api/v1/platform/session/me")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_login_returns_token_after_bootstrap(client, db_session):
    from otm_workbench.platform.services import bootstrap_admin

    bootstrap_admin(db_session, email="admin@example.com", password="ChangeMe123!")

    response = client.post(
        "/api/v1/platform/session/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_current_user_returns_authenticated_user(client, admin_header):
    response = client.get("/api/v1/platform/session/me", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"
    assert response.json()["is_admin"] is True


def test_capability_guard_returns_403_without_capability(client, auth_header):
    response = client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=auth_header,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
