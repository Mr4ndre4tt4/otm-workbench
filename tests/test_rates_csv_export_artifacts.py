def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic export batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def add_accessorial_table(client, admin_header, batch_id):
    return client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_001",
                            "COST_CODE_GID": "OTM1.ACC_FUEL",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_export_rejects_unvalidated_batch(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "validated" in response.json()["message"].lower()


def test_export_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["message"].lower()
