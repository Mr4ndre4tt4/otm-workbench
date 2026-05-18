import json

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanZipAnalysis, Manifest


def test_load_plan_zip_analyses_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_zip_analyses" in tables


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic ZIP analysis batch", "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001", extra_fields=None):
    row = {
        "ACCESSORIAL_COST_GID": f"OTM1.{xid}",
        "ACCESSORIAL_COST_XID": xid,
    }
    if extra_fields:
        row.update(extra_fields)
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={"tables": [{"table_name": "ACCESSORIAL_COST", "rows": [row]}]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def prepare_registered_load_plan_package(client, admin_header, extra_fields=None):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"], extra_fields=extra_fields)
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic ZIP analysis package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def test_zip_analysis_succeeds_for_registered_package(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    analysis = db_session.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == payload["id"]).one()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "ANALYZED"
    assert payload["source_artifact_id"] == export["artifact_id"]
    assert payload["source_manifest_id"] == export["manifest_id"]
    assert payload["summary"]["csv_file_count"] == 1
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["warning_count"] == 0
    assert payload["findings"] == []
    assert analysis.created_by == "admin@example.com"
    assert analysis.analyzed_at is not None


def test_zip_analysis_creates_manifest_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.zip_analysis.run").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.zip_analysis.completed").one()
    manifest_json = json.loads(manifest.manifest_json)

    assert manifest_json["manifest_type"] == "zip_analysis"
    assert manifest_json["package"]["id"] == package["id"]
    assert manifest_json["files"][0]["table_name"] == "ACCESSORIAL_COST"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "load_plan_zip_analysis"
    assert evidence.artifact_id == export["artifact_id"]
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_zip_analysis_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/zip-analysis", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/zip-analysis/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["summary"]["package_type"] == "rates_csv_zip"
