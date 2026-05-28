import json
from pathlib import Path
import zipfile

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import (
    Artifact,
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanReadinessExport,
    Manifest,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": scenario_code,
            "name": "Synthetic readiness export batch",
            "domain_name": "OTM1",
            "project_id": "project_readiness_export",
            "profile_id": "profile_readiness_export",
            "environment_id": "env_readiness_export",
        },
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
        json={"approval_note": "Reviewed for synthetic readiness export"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}", headers=admin_header)
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def create_cutover_readiness(client, admin_header):
    _batch, _export, _approval, package = prepare_registered_load_plan_package(client, admin_header)
    readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert readiness.status_code == 200
    return package, readiness.json()["items"][0]


def test_load_plan_readiness_exports_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_readiness_exports" in tables


def test_readiness_export_rejects_missing_readiness(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/missing_readiness/export",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_readiness_export_creates_zip_artifact_manifest_evidence_audit_event(
    client,
    admin_header,
    db_session,
):
    package, readiness = create_cutover_readiness(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    export = db_session.query(LoadPlanReadinessExport).filter_by(id=payload["id"]).one()
    artifact = db_session.query(Artifact).filter_by(id=export.artifact_id).one()
    manifest = db_session.query(Manifest).filter_by(id=export.manifest_id).one()
    evidence = db_session.query(Evidence).filter_by(id=export.evidence_id).one()
    audit = db_session.query(AuditLog).filter_by(action="load_plan.readiness_export.export").one()
    event = db_session.query(DomainEvent).filter_by(event_type="load_plan.readiness_export.exported").one()

    assert payload["package_id"] == package["id"]
    assert payload["readiness_id"] == readiness["id"]
    assert payload["status"] == "EXPORTED"
    assert payload["summary"]["readiness_status"] == "MISSING_SEQUENCE"
    assert payload["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        payload["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert artifact.artifact_type == "load_plan_readiness_export_zip"
    assert artifact.project_id == "project_readiness_export"
    assert artifact.profile_id == "profile_readiness_export"
    assert artifact.environment_id == "env_readiness_export"
    assert artifact.domain_name == "OTM1"
    assert artifact.visibility == "PROJECT"
    assert artifact.content_type == "application/zip"
    assert artifact.sensitivity_level == "internal"
    assert Path(artifact.file_path).exists()
    assert manifest.source_module == "load_plan"
    assert manifest.project_id == "project_readiness_export"
    assert manifest.profile_id == "profile_readiness_export"
    assert manifest.environment_id == "env_readiness_export"
    assert manifest.domain_name == "OTM1"
    assert manifest.visibility == "PROJECT"
    assert evidence.evidence_type == "load_plan_readiness_export"
    assert evidence.client_safe is True
    assert evidence.project_id == "project_readiness_export"
    assert evidence.profile_id == "profile_readiness_export"
    assert evidence.environment_id == "env_readiness_export"
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    evidence_summary = json.loads(evidence.summary_json)
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        evidence_summary["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert audit_metadata["catalog_macro_object_code"] == "RATE_RECORD"
    assert audit_metadata["project_id"] == "project_readiness_export"
    assert audit_metadata["environment_id"] == "env_readiness_export"
    assert audit_metadata["domain_name"] == "OTM1"
    assert event_payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["project_id"] == "project_readiness_export"
    assert event_payload["environment_id"] == "env_readiness_export"
    assert event_payload["domain_name"] == "OTM1"
    assert (
        event_payload["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert audit.target_id == export.id
    assert event.aggregate_id == export.id


def test_readiness_export_zip_contains_manifest_readiness_and_blockers(
    client,
    admin_header,
    db_session,
):
    _package, readiness = create_cutover_readiness(client, admin_header)
    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )
    assert response.status_code == 200

    artifact = db_session.query(Artifact).filter_by(id=response.json()["artifact_id"]).one()
    with zipfile.ZipFile(artifact.file_path) as archive:
        assert sorted(archive.namelist()) == ["blockers.json", "manifest.json", "readiness.json"]
        manifest = json.loads(archive.read("manifest.json"))
        readiness_payload = json.loads(archive.read("readiness.json"))
        blockers = json.loads(archive.read("blockers.json"))

    assert manifest["schema_version"] == "load-plan-readiness-export-manifest/v1"
    assert manifest["source_entity_id"] == readiness["id"]
    assert manifest["catalog_macro_object_code"] == "RATE_RECORD"
    assert manifest["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert {item["path"] for item in manifest["files"]} == {"readiness.json", "blockers.json"}
    assert readiness_payload["id"] == readiness["id"]
    assert readiness_payload["status"] == "MISSING_SEQUENCE"
    assert blockers[0]["code"] == "SEQUENCE_SNAPSHOT_MISSING"


def test_readiness_export_reexport_creates_new_export_and_artifact(
    client,
    admin_header,
    db_session,
):
    _package, readiness = create_cutover_readiness(client, admin_header)

    first = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["artifact_id"] != second.json()["artifact_id"]
    first_artifact = db_session.query(Artifact).filter_by(id=first.json()["artifact_id"]).one()
    second_artifact = db_session.query(Artifact).filter_by(id=second.json()["artifact_id"]).one()
    assert first_artifact.file_path != second_artifact.file_path
    assert db_session.query(LoadPlanReadinessExport).count() == 2


def test_readiness_export_preserves_readiness_status(client, admin_header):
    _package, readiness = create_cutover_readiness(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["summary"]["readiness_status"] == "MISSING_SEQUENCE"


def test_readiness_export_metadata_does_not_include_raw_values_or_notes(
    client,
    admin_header,
    db_session,
):
    _package, readiness = create_cutover_readiness(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    export = db_session.query(LoadPlanReadinessExport).filter_by(id=response.json()["id"]).one()
    evidence = db_session.query(Evidence).filter_by(id=export.evidence_id).one()
    audit = db_session.query(AuditLog).filter_by(action="load_plan.readiness_export.export").one()
    event = db_session.query(DomainEvent).filter_by(event_type="load_plan.readiness_export.exported").one()
    combined = "\n".join(
        [export.summary_json, evidence.summary_json, audit.metadata_json, event.payload_json]
    )

    assert "OTM1.ACC_COST_001" not in combined
    assert "Reviewed for synthetic readiness export" not in combined


def test_readiness_export_list_detail_and_filters(client, admin_header):
    package, readiness = create_cutover_readiness(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/cutover-readiness/exports", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports",
        params={"package_id": package["id"], "readiness_id": readiness["id"], "status": "EXPORTED"},
        headers=admin_header,
    )
    catalog_matched = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/exports/{created['id']}",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert catalog_matched.status_code == 200
    assert catalog_unmatched.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert catalog_matched.json()["total"] == 1
    assert catalog_matched.json()["items"][0]["id"] == created["id"]
    assert catalog_unmatched.json()["total"] == 0
    assert catalog_unmatched.json()["items"] == []
    assert catalog_unmatched.json()["code"] == "UNSUPPORTED_CATALOG_MACRO_OBJECT"
    assert catalog_unmatched.json()["message"] == "Catalog macro-object is outside the Load Plan package scope."
    assert catalog_unmatched.json()["details"] == {"catalog_macro_object_code": "LOCATION"}
    assert catalog_unmatched.json()["catalog_macro_object_code"] == "LOCATION"
    assert detail.json()["id"] == created["id"]


def test_readiness_export_detail_rejects_missing_export(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports/missing_export",
        headers=admin_header,
    )

    assert response.status_code == 404
