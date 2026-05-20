def test_user_preferences_default_to_light_mode(client, admin_header):
    response = client.get("/api/v1/platform/user-preferences", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["theme_mode"] == "light"
    assert payload["follow_system_theme"] is False
    assert payload["density"] == "comfortable"
    assert payload["sidebar_mode"] == "expanded"
    assert payload["updated_at"]
    assert payload["user_id"]


def test_user_preferences_can_be_updated_and_read_back(client, admin_header):
    updated = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "dark",
            "follow_system_theme": True,
            "density": "compact",
            "sidebar_mode": "collapsed",
        },
        headers=admin_header,
    )
    current = client.get("/api/v1/platform/user-preferences", headers=admin_header)

    assert updated.status_code == 200
    assert current.status_code == 200
    payload = current.json()
    assert payload["theme_mode"] == "dark"
    assert payload["follow_system_theme"] is True
    assert payload["density"] == "compact"
    assert payload["sidebar_mode"] == "collapsed"


def test_user_preferences_reject_invalid_theme_mode(client, admin_header):
    response = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "sepia",
            "follow_system_theme": False,
            "density": "comfortable",
            "sidebar_mode": "expanded",
        },
        headers=admin_header,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
