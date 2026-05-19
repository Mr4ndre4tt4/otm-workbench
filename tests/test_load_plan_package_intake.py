import json

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanPackage


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic load package batch", "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001"):
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": f"OTM1.{xid}",
                            "ACCESSORIAL_COST_XID": xid,
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def prepare_approved_exported_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic load package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    return batch, export.json(), approval.json()


def test_load_plan_packages_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_packages" in tables


def test_register_rejects_unapproved_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "approved" in response.json()["message"].lower()


def test_register_rejects_approved_rate_batch_without_export(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Approved without export for negative test"},
        headers=admin_header,
    )
    assert approval.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "export" in response.json()["message"].lower()


def test_register_rates_package_creates_load_plan_package(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    package = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload["id"]).one()
    assert payload["source_module"] == "rates"
    assert payload["source_entity_type"] == "rate_batch"
    assert payload["source_entity_id"] == batch["id"]
    assert payload["package_type"] == "rates_csv_zip"
    assert payload["status"] == "REGISTERED"
    assert payload["artifact_id"] == export["artifact_id"]
    assert payload["manifest_id"] == export["manifest_id"]
    assert payload["approval_evidence_id"] == approval["evidence_id"]
    assert payload["load_sequence"] == [
        {
            "position": 6,
            "table_name": "ACCESSORIAL_COST",
            "row_count": 1,
            "requirement_level": "REQUIRED",
        }
    ]
    assert package.created_by == "admin@example.com"
    assert package.registered_at is not None


def test_load_plan_package_list_and_detail(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/packages", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/packages/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["artifact_id"] == export["artifact_id"]
    assert detail.json()["approval_evidence_id"] == approval["evidence_id"]
    assert detail.json()["summary"]["scenario_code"] == "ACCESSORIAL_ONLY"
    assert "OTM1.ACC_COST_001" not in json.dumps(detail.json())


def test_load_plan_summary_counts_packages(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get("/api/v1/modules/load-plan/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["registered_packages"] == 1
    assert payload["by_source_module"] == {"rates": 1}
    assert payload["by_status"] == {"REGISTERED": 1}
    assert payload["by_catalog_macro_object"] == {
        "RATE_RECORD": {
            "package_count": 1,
            "catalog_load_plan_path": "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
        }
    }
    assert payload["next_actions"] == ["build_csvutil"]


def test_load_plan_module_is_registered(client, admin_header):
    modules = client.get("/api/v1/platform/modules", headers=admin_header)

    assert modules.status_code == 200
    module_ids = [item["id"] for item in modules.json()["items"]]
    assert "load_plan" in module_ids


def test_register_rates_package_creates_client_safe_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").one()
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)

    assert evidence.source_module == "load_plan"
    assert evidence.evidence_type == "load_plan_package_intake"
    assert evidence.client_safe is True
    assert evidence.artifact_id == export["artifact_id"]
    assert evidence.manifest_id == export["manifest_id"]
    assert approval["evidence_id"] in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit_metadata["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_register_rates_package_is_idempotent(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    first = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(LoadPlanPackage).count() == 1
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "load_plan_package_intake").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").count() == 1
