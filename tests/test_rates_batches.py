from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable


def test_rate_batch_models_persist(db_session):
    batch = RateBatch(
        project_id="project_otm1",
        environment_id="uat",
        profile_id="profile_otm1",
        scenario_code="RATE_GEO_ONLY",
        name="Synthetic rate geo batch",
        domain_name="OTM1",
        source_type="api",
        created_by="codex",
    )
    db_session.add(batch)
    db_session.flush()

    table = RateBatchTable(
        batch_id=batch.id,
        table_name="RATE_GEO",
        sequence_index=4,
        requirement_level="REQUIRED",
        row_count=1,
        status="PENDING",
    )
    db_session.add(table)
    db_session.flush()

    row = RateBatchRow(
        batch_id=batch.id,
        batch_table_id=table.id,
        table_name="RATE_GEO",
        row_index=1,
        row_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        normalized_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        row_hash="hash",
        status="PENDING",
    )
    db_session.add(row)
    db_session.flush()

    issue = RateBatchIssue(
        batch_id=batch.id,
        batch_table_id=table.id,
        batch_row_id=row.id,
        severity="INFO",
        issue_code="ROW_ACCEPTED",
        table_name="RATE_GEO",
        column_name="RATE_GEO_GID",
        message="Row accepted.",
        details_json="{}",
    )
    db_session.add(issue)
    db_session.commit()

    assert db_session.query(RateBatch).count() == 1
    assert db_session.query(RateBatchTable).count() == 1
    assert db_session.query(RateBatchRow).count() == 1
    assert db_session.query(RateBatchIssue).count() == 1


def test_create_rate_batch_api(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
            "project_id": "project_otm1",
            "environment_id": "uat",
            "profile_id": "profile_otm1",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_code"] == "RATE_GEO_ONLY"
    assert payload["status"] == "DRAFT"
    assert payload["domain_name"] == "OTM1"


def test_add_rate_batch_tables_api_sorts_by_rates_sequence(client, admin_header):
    created = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/rates/batches/{created['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "RATE_GEO_COST",
                    "rows": [
                        {
                            "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001",
                            "CHARGE_AMOUNT": 10,
                        }
                    ],
                },
                {
                    "table_name": "X_LANE",
                    "rows": [{"X_LANE_GID": "OTM1.RG_001", "X_LANE_XID": "RG_001"}],
                },
            ]
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert [item["table_name"] for item in response.json()["tables"]] == [
        "X_LANE",
        "RATE_GEO_COST",
    ]
