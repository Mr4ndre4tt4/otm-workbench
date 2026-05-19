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
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanSequenceSnapshot,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic readiness batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic cutover readiness"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def rewrite_export_with_unknown_column(db_session, export):
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".cutover-readiness.zip")
    with zipfile.ZipFile(artifact_path) as original:
        entries = {
            name: original.read(name)
            for name in original.namelist()
            if name != "csv/001_ACCESSORIAL_COST.csv"
        }
    entries["csv/001_ACCESSORIAL_COST.csv"] = (
        "ACCESSORIAL_COST\n"
        "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID,SYNTHETIC_UNKNOWN_COLUMN\n"
        "OTM1.ACC_COST_001,ACC_COST_001,DEMO\n"
    ).encode("utf-8")
    with zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as rewritten:
        for name, content in entries.items():
            rewritten.writestr(name, content)
    artifact.file_path = str(rewritten_path)
    artifact.file_name = rewritten_path.name
    artifact.size_bytes = rewritten_path.stat().st_size
    db_session.commit()


def create_sequence_snapshot(client, admin_header, package):
    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_load_plan_cutover_readiness_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_cutover_readiness" in tables


def test_cutover_readiness_generate_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_cutover_readiness_missing_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["package_count"] == 1
    item = payload["items"][0]
    assert item["package_id"] == package["id"]
    assert item["sequence_snapshot_id"] is None
    assert item["status"] == "MISSING_SEQUENCE"
    assert item["blockers"][0]["code"] == "SEQUENCE_SNAPSHOT_MISSING"
    assert "generate_sequence_snapshot" in payload["summary"]["next_actions"]


def test_cutover_readiness_blocked_from_blocked_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    snapshot = create_sequence_snapshot(client, admin_header, package)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["sequence_snapshot_id"] == snapshot["id"]
    assert item["status"] == "BLOCKED"
    assert item["summary"]["error_count"] > 0
    assert "resolve_sequence_blockers" in response.json()["summary"]["next_actions"]


def test_cutover_readiness_ready_from_blocker_free_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package_model.project_id,
        environment_id=package_model.environment_id,
        profile_id=package_model.profile_id,
        package_id=package["id"],
        status="READY_FOR_REVIEW",
        sequence_json=json.dumps(
            [{"position": 1, "table_name": "ACCESSORIAL_COST", "row_count": 1, "requirement_level": "OPTIONAL"}],
            sort_keys=True,
        ),
        blockers_json="[]",
        summary_json=json.dumps({"blocker_count": 0, "error_count": 0, "warning_count": 0}, sort_keys=True),
        generated_by="admin@example.com",
    )
    db_session.add(snapshot)
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["sequence_snapshot_id"] == snapshot.id
    assert item["status"] == "READY"
    assert item["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        item["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert "ready_for_cutover_export" in response.json()["summary"]["next_actions"]


def test_cutover_readiness_needs_review_from_warning_only_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package_model.project_id,
        environment_id=package_model.environment_id,
        profile_id=package_model.profile_id,
        package_id=package["id"],
        status="BLOCKED",
        sequence_json="[]",
        blockers_json=json.dumps(
            [
                {
                    "code": "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER",
                    "severity": "WARNING",
                    "table_name": "ACCESSORIAL_COST",
                    "source_type": "load_plan_review_decision",
                    "source_id": "synthetic_decision",
                    "message": "Synthetic exclusion requires review.",
                    "details": {},
                }
            ],
            sort_keys=True,
        ),
        summary_json=json.dumps({"blocker_count": 1, "error_count": 0, "warning_count": 1}, sort_keys=True),
        generated_by="admin@example.com",
    )
    db_session.add(snapshot)
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["status"] == "NEEDS_REVIEW"
    assert item["summary"]["warning_count"] == 1
    assert "review_warnings" in response.json()["summary"]["next_actions"]


def test_cutover_readiness_creates_evidence_audit_event_without_raw_values(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    create_sequence_snapshot(client, admin_header, package)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    readiness = (
        db_session.query(LoadPlanCutoverReadiness)
        .filter(LoadPlanCutoverReadiness.id == response.json()["items"][0]["id"])
        .one()
    )
    evidence = db_session.query(Evidence).filter(Evidence.id == readiness.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.cutover_readiness.generate").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.cutover_readiness.generated").one()
    readiness_summary = json.loads(readiness.summary_json)
    evidence_summary = json.loads(evidence.summary_json)
    assert evidence.evidence_type == "load_plan_cutover_readiness"
    assert evidence.client_safe is True
    assert readiness_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        evidence_summary["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert audit.target_id == readiness.id
    assert event.aggregate_id == readiness.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
    assert "Synthetic" not in evidence.summary_json


def test_cutover_readiness_list_detail_latest_and_filters(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    create_sequence_snapshot(client, admin_header, package)
    created = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()["items"][0]

    listed = client.get("/api/v1/modules/load-plan/cutover-readiness", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/cutover-readiness",
        params={"package_id": package["id"], "status": "BLOCKED"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/cutover-readiness/{created['id']}", headers=admin_header)
    latest = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/latest",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert latest.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert detail.json()["id"] == created["id"]
    assert latest.json()["id"] == created["id"]


def test_cutover_readiness_aggregate_generation(client, admin_header, db_session):
    first_batch, first_export, first_approval, first_package = prepare_registered_load_plan_package(client, admin_header)
    second_batch = create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY")
    add_accessorial_table(client, admin_header, second_batch["id"], xid="ACC_COST_002")
    preview = client.post(f"/api/v1/modules/rates/batches/{second_batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    second_export = client.post(f"/api/v1/modules/rates/batches/{second_batch['id']}/export-csv", headers=admin_header)
    assert second_export.status_code == 200
    second_approval = client.post(
        f"/api/v1/modules/rates/batches/{second_batch['id']}/approve",
        json={"approval_note": "Reviewed for second synthetic readiness package"},
        headers=admin_header,
    )
    assert second_approval.status_code == 200
    second_package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{second_batch['id']}",
        headers=admin_header,
    )
    assert second_package.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["summary"]["package_count"] == 2
    assert len(response.json()["items"]) == 2
    assert db_session.query(LoadPlanCutoverReadiness).count() == 2
