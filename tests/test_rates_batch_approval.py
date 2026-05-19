import json

from otm_workbench.models import AuditLog, DomainEvent, Evidence, RateBatch, RateBatchIssue


def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic approval batch", "domain_name": "OTM1"},
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
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_readiness_returns_blockers_for_draft_batch(client, admin_header):
    batch = create_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready_for_approval"] is False
    assert payload["ready_for_export"] is False
    assert "BATCH_NOT_VALIDATED" in payload["blockers"]
    assert "NO_TABLES" in payload["blockers"]
    assert "NO_ROWS" in payload["blockers"]
    assert payload["issue_summary"] == {"errors": 0, "warnings": 0, "infos": 0}


def test_readiness_returns_counts_and_export_flag(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )
    assert export.status_code == 200

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready_for_approval"] is True
    assert payload["ready_for_export"] is True
    assert payload["table_count"] == 1
    assert payload["row_count"] == 1
    assert payload["has_export_artifact"] is True
    assert payload["blockers"] == []
    assert payload["next_actions"] == ["approve"]


def test_approval_rejects_draft_batch(client, admin_header):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic package"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "not ready" in response.json()["message"].lower()


def test_approval_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic package"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["message"].lower()


def test_approval_succeeds_with_warnings_and_sets_status(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    db_session.add(
        RateBatchIssue(
            batch_id=batch["id"],
            severity="WARNING",
            issue_code="SYNTHETIC_WARNING",
            table_name="ACCESSORIAL_COST",
            message="Synthetic warning for approval readiness.",
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic package"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPROVED"
    assert payload["approved_at"] is not None
    assert payload["approved_by"] == "admin@example.com"
    assert payload["readiness"]["issue_summary"]["warnings"] == 1
    refreshed_batch = db_session.query(RateBatch).filter(RateBatch.id == batch["id"]).one()
    summary = json.loads(refreshed_batch.summary_json)
    assert refreshed_batch.status == "APPROVED"
    assert refreshed_batch.approved_at is not None
    assert summary["approval"]["approved_by"] == "admin@example.com"
    assert summary["approval"]["approval_note"] == "Reviewed for synthetic package"


def test_approval_creates_evidence_audit_and_event(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )
    assert export.status_code == 200

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic package"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.approve").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "rates.batch.approved").one()
    evidence_summary = json.loads(evidence.summary_json)
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)

    assert payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "rates_batch_approval"
    assert evidence.artifact_id == export.json()["artifact_id"]
    assert evidence.manifest_id == export.json()["manifest_id"]
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert audit_metadata["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == batch["id"]
    assert event.aggregate_id == batch["id"]
    assert event.status == "PENDING"


def test_repeated_approval_is_idempotent(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)

    first = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed once"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed twice"},
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "rates_batch_approval").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.approve").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "rates.batch.approved").count() == 1
