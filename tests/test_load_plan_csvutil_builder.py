import json
from pathlib import Path

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import Artifact, AuditLog, CsvutilBuild, DomainEvent, Evidence, LoadPlanPackage, Manifest


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic CSVUTIL batch", "domain_name": "OTM1"},
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


def prepare_registered_load_plan_package(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic CSVUTIL package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def test_csvutil_builds_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "csvutil_builds" in tables


def test_csvutil_build_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_csvutil_build_succeeds_for_registered_package(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    build = db_session.query(CsvutilBuild).filter(CsvutilBuild.id == payload["id"]).one()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "BUILT"
    assert payload["ctl_artifact_id"]
    assert payload["cl_artifact_id"]
    assert payload["manifest_id"]
    assert payload["evidence_id"]
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["package_type"] == "rates_csv_zip"
    assert payload["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        payload["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert build.created_by == "admin@example.com"
    assert build.built_at is not None


def test_registered_rates_package_includes_catalog_context(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == package["evidence_id"]).one()
    package_summary = json.loads(package_row.summary_json)
    evidence_summary = json.loads(evidence.summary_json)

    assert package["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        package["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert package_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        evidence_summary["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )


def test_csvutil_build_creates_ctl_cl_manifest_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    ctl = db_session.query(Artifact).filter(Artifact.id == payload["ctl_artifact_id"]).one()
    cl = db_session.query(Artifact).filter(Artifact.id == payload["cl_artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.csvutil.build").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.csvutil.built").one()

    ctl_text = Path(ctl.file_path).read_text(encoding="utf-8")
    cl_text = Path(cl.file_path).read_text(encoding="utf-8")
    manifest_json = json.loads(manifest.manifest_json)

    assert ctl.artifact_type == "csvutil_ctl"
    assert cl.artifact_type == "csvutil_cl"
    assert ctl.content_type == "text/plain"
    assert cl.content_type == "text/plain"
    assert "001,ACCESSORIAL_COST,csv/001_ACCESSORIAL_COST.csv" in ctl_text
    assert "LOAD ACCESSORIAL_COST FROM csv/001_ACCESSORIAL_COST.csv" in cl_text
    assert "OTM1.ACC_COST_001" not in ctl_text
    assert "OTM1.ACC_COST_001" not in cl_text
    assert manifest_json["manifest_type"] == "csvutil_build"
    assert manifest_json["package"]["id"] == package["id"]
    assert manifest_json["package"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert {item["artifact_type"] for item in manifest_json["files"]} == {"csvutil_ctl", "csvutil_cl"}
    assert evidence.client_safe is True
    assert evidence.evidence_type == "csvutil_build"
    assert evidence.artifact_id == ctl.id
    evidence_summary = json.loads(evidence.summary_json)
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        evidence_summary["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert audit_metadata["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_csvutil_build_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/csvutil/builds", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/csvutil/builds/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["summary"]["package_type"] == "rates_csv_zip"


def test_csvutil_build_rejects_package_without_artifact_or_manifest(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = None
    package_row.manifest_id = None
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "artifact" in response.json()["message"].lower()


def test_csvutil_build_rejects_empty_load_sequence(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.load_sequence_json = "[]"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "load sequence" in response.json()["message"].lower()


def test_csvutil_rebuild_creates_separate_build_history(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    first = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    second = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert db_session.query(CsvutilBuild).count() == 2
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "csvutil_build").count() == 2
