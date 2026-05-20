import json
from pathlib import Path

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import Artifact, AuditLog, CsvutilBuild, DomainEvent, Evidence, LoadPlanPackage, Manifest
from tests.test_load_plan_cutover_checklist import create_client_safe_evidence


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


def test_csvutil_build_accepts_parameter_set(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={
            "package_id": package["id"],
            "parameter_set": {
                "mode": "INSERT",
                "delimiter": "PIPE",
                "encoding": "UTF-8",
                "date_format": "YYYY-MM-DD HH24:MI:SS",
            },
        },
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
    evidence_summary = json.loads(evidence.summary_json)

    assert "# csvutil_mode=INSERT" in ctl_text
    assert "# delimiter=PIPE" in ctl_text
    assert "# encoding=UTF-8" in ctl_text
    assert "# date_format=YYYY-MM-DD HH24:MI:SS" in ctl_text
    assert "SET MODE INSERT" in cl_text
    assert "SET DELIMITER PIPE" in cl_text
    assert payload["summary"]["parameter_set"]["mode"] == "INSERT"
    assert payload["summary"]["parameter_set"]["delimiter"] == "PIPE"
    assert manifest_json["parameter_set"] == payload["summary"]["parameter_set"]
    assert evidence_summary["parameter_set"]["delimiter"] == "PIPE"
    assert json.loads(audit.metadata_json)["parameter_set"]["mode"] == "INSERT"
    assert json.loads(event.payload_json)["parameter_set"]["date_format"] == "YYYY-MM-DD HH24:MI:SS"


def test_csvutil_build_rejects_invalid_parameter_set(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"], "parameter_set": {"mode": "DELETE"}},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "mode" in response.json()["message"].lower()


def test_csvutil_build_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/csvutil/builds", headers=admin_header)
    catalog_matched = client.get(
        "/api/v1/modules/load-plan/csvutil/builds",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/load-plan/csvutil/builds",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/csvutil/builds/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert catalog_matched.status_code == 200
    assert catalog_unmatched.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert catalog_matched.json()["total"] == 1
    assert catalog_matched.json()["items"][0]["id"] == created["id"]
    assert catalog_unmatched.json()["total"] == 0
    assert catalog_unmatched.json()["items"] == []
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


def test_csvutil_build_from_cutover_checklist_uses_done_csvutil_items(
    client,
    admin_header,
    db_session,
):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    table_item = next(item for item in checklist["items"] if item["item_code"] == "TABLE_READY")
    evidence = create_client_safe_evidence(db_session, checklist["id"], table_item["table_name"])
    updated = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{table_item['id']}",
        json={"status": "DONE", "method": "CSVUTIL", "evidence_id": evidence.id},
        headers=admin_header,
    )
    assert updated.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    manifest_json = json.loads(manifest.manifest_json)
    evidence_row = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.csvutil.build").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.csvutil.built").one()

    assert payload["package_id"] == package["id"]
    assert payload["summary"]["source_entity_type"] == "cutover_checklist"
    assert payload["summary"]["source_entity_id"] == checklist["id"]
    assert payload["summary"]["checklist_id"] == checklist["id"]
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["selected_item_count"] == 1
    assert manifest_json["source_entity_type"] == "cutover_checklist"
    assert manifest_json["source_entity_id"] == checklist["id"]
    assert manifest_json["package"]["id"] == package["id"]
    assert manifest_json["load_sequence"][0]["table_name"] == "ACCESSORIAL_COST"
    assert evidence_row.client_safe is True
    assert json.loads(evidence_row.summary_json)["checklist_id"] == checklist["id"]
    assert json.loads(audit.metadata_json)["checklist_id"] == checklist["id"]
    assert json.loads(event.payload_json)["checklist_id"] == checklist["id"]
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert "OTM1.ACC_COST_001" not in evidence_row.summary_json


def test_csvutil_build_from_cutover_checklist_accepts_parameter_set(
    client,
    admin_header,
    db_session,
):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    table_item = next(item for item in checklist["items"] if item["item_code"] == "TABLE_READY")
    evidence = create_client_safe_evidence(db_session, checklist["id"], table_item["table_name"])
    updated = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{table_item['id']}",
        json={"status": "DONE", "method": "CSVUTIL", "evidence_id": evidence.id},
        headers=admin_header,
    )
    assert updated.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        json={"parameter_set": {"mode": "INSERT", "delimiter": "COMMA", "encoding": "UTF-8"}},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    assert payload["summary"]["checklist_id"] == checklist["id"]
    assert payload["summary"]["parameter_set"]["delimiter"] == "COMMA"
    assert json.loads(manifest.manifest_json)["parameter_set"]["mode"] == "INSERT"


def test_csvutil_build_from_cutover_checklist_accepts_table_overrides(
    client,
    admin_header,
    db_session,
):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    table_item = next(item for item in checklist["items"] if item["item_code"] == "TABLE_READY")
    evidence = create_client_safe_evidence(db_session, checklist["id"], table_item["table_name"])
    updated = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{table_item['id']}",
        json={"status": "DONE", "method": "CSVUTIL", "evidence_id": evidence.id},
        headers=admin_header,
    )
    assert updated.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        json={
            "parameter_set": {"mode": "INSERT", "delimiter": "COMMA"},
            "table_overrides": {"ACCESSORIAL_COST": {"mode": "UPDATE", "delimiter": "PIPE"}},
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    ctl = db_session.query(Artifact).filter(Artifact.id == payload["ctl_artifact_id"]).one()
    cl = db_session.query(Artifact).filter(Artifact.id == payload["cl_artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence_row = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.csvutil.build").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.csvutil.built").one()

    ctl_text = Path(ctl.file_path).read_text(encoding="utf-8")
    cl_text = Path(cl.file_path).read_text(encoding="utf-8")
    manifest_json = json.loads(manifest.manifest_json)
    evidence_summary = json.loads(evidence_row.summary_json)

    assert "# table_override ACCESSORIAL_COST mode=UPDATE delimiter=PIPE" in ctl_text
    assert "LOAD ACCESSORIAL_COST FROM csv/001_ACCESSORIAL_COST.csv MODE UPDATE DELIMITER PIPE" in cl_text
    assert payload["summary"]["table_overrides"]["ACCESSORIAL_COST"]["mode"] == "UPDATE"
    assert payload["summary"]["table_overrides"]["ACCESSORIAL_COST"]["delimiter"] == "PIPE"
    assert manifest_json["table_overrides"] == payload["summary"]["table_overrides"]
    assert evidence_summary["table_overrides"]["ACCESSORIAL_COST"]["mode"] == "UPDATE"
    assert json.loads(audit.metadata_json)["table_overrides"]["ACCESSORIAL_COST"]["delimiter"] == "PIPE"
    assert json.loads(event.payload_json)["table_overrides"]["ACCESSORIAL_COST"]["mode"] == "UPDATE"
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json


def test_csvutil_build_from_cutover_checklist_rejects_unknown_table_override(
    client,
    admin_header,
    db_session,
):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    table_item = next(item for item in checklist["items"] if item["item_code"] == "TABLE_READY")
    evidence = create_client_safe_evidence(db_session, checklist["id"], table_item["table_name"])
    updated = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{table_item['id']}",
        json={"status": "DONE", "method": "CSVUTIL", "evidence_id": evidence.id},
        headers=admin_header,
    )
    assert updated.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        json={"table_overrides": {"RATE_GEO_COST": {"mode": "UPDATE"}}},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "override" in response.json()["message"].lower()


def test_csvutil_build_from_cutover_checklist_rejects_without_done_csvutil_items(
    client,
    admin_header,
):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "eligible" in response.json()["message"].lower()
