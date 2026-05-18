def create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def test_validation_errors_when_required_table_missing(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={"tables": [{"table_name": "X_LANE", "rows": [{"X_LANE_GID": "OTM1.RG_001"}]}]},
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "REQUIRED_TABLE_MISSING" for issue in payload["issues"])


def test_validation_rejects_unknown_column(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY")
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [{"ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001", "NOT_A_COLUMN": "x"}],
                }
            ]
        },
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "UNKNOWN_COLUMN" for issue in payload["issues"])


def test_batch_issues_endpoint_returns_persisted_issues(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/issues",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] >= 1
