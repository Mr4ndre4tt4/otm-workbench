def create_batch(client, admin_header, name="Synthetic summary batch", scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": name, "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id):
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_001",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def action_by_key(actions, key):
    return next(action for action in actions if action["key"] == key)


def count_by_key(counts, key):
    return next(count for count in counts if count["key"] == key)


def test_rates_summary_returns_empty_module_read_model(client, admin_header):
    response = client.get("/api/v1/modules/rates/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "rates"
    assert payload["status"] == "ok"
    assert payload["title"] == "Rates Studio"
    assert payload["primary_object"] == "rate_batch"
    assert count_by_key(payload["counts"], "total")["value"] == 0
    assert count_by_key(payload["counts"], "blocked")["value"] == 0
    assert payload["recent_objects"] == []
    assert payload["open_blockers"] == []
    assert payload["recent_artifacts"] == []
    create = action_by_key(payload["available_actions"], "create_batch")
    assert create["method"] == "POST"
    assert create["href"] == "/api/v1/modules/rates/batches"
    assert create["disabled"] is False


def test_rates_summary_reports_counts_recent_objects_and_client_safe_blockers(client, admin_header):
    blocked_batch = create_batch(client, admin_header, name="Synthetic blocked batch")
    ready_batch = create_batch(client, admin_header, name="Synthetic ready batch")
    add_accessorial_table(client, admin_header, ready_batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{ready_batch['id']}/csv-preview", headers=admin_header)

    response = client.get("/api/v1/modules/rates/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert count_by_key(payload["counts"], "total")["value"] == 2
    assert count_by_key(payload["counts"], "ready_for_approval")["value"] == 1
    assert count_by_key(payload["counts"], "blocked")["value"] == 1
    assert {item["id"] for item in payload["recent_objects"]} == {blocked_batch["id"], ready_batch["id"]}
    ready = next(item for item in payload["recent_objects"] if item["id"] == ready_batch["id"])
    assert ready["display_name"] == "Synthetic ready batch"
    assert ready["status"] == "EXPORT_PREVIEWED"
    assert action_by_key(ready["available_actions"], "approve")["disabled"] is False
    blockers = payload["open_blockers"]
    assert blockers == [
        {
            "object_id": blocked_batch["id"],
            "object_type": "rate_batch",
            "severity": "warning",
            "codes": ["BATCH_NOT_VALIDATED", "NO_TABLES", "NO_ROWS"],
            "message": "Rate batch is not ready: BATCH_NOT_VALIDATED;NO_TABLES;NO_ROWS",
        }
    ]
    assert "OTM1.ACC_COST_001" not in str(payload)
