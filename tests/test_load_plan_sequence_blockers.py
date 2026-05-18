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
    LoadPlanPackage,
    LoadPlanReviewDecision,
    LoadPlanSequenceSnapshot,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic sequence batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic sequence package"},
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
    rewritten_path = artifact_path.with_suffix(".sequence-blockers.zip")
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


def create_zip_analysis(client, admin_header, package):
    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def create_review_item(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)
    review = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )
    assert review.status_code == 200
    return package, analysis, review.json()["items"][0]


def test_load_plan_sequence_snapshots_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_sequence_snapshots" in tables


def test_sequence_snapshot_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_sequence_snapshot_creates_snapshot_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "BLOCKED"
    assert payload["generated_by"] == "admin@example.com"
    assert payload["sequence"][0]["table_name"] == "ACCESSORIAL_COST"
    assert payload["sequence"][0]["dictionary_table_found"] is True
    assert "ACCESSORIAL_CODE" in payload["sequence"][0]["parent_tables"]
    assert "ACCESSORIAL_CODE" in payload["sequence"][0]["missing_parent_tables_in_package"]
    assert "ZIP_ANALYSIS_MISSING" in [item["code"] for item in payload["blockers"]]
    assert "PACKAGE_PARENT_TABLE_MISSING" in [item["code"] for item in payload["blockers"]]
    snapshot = db_session.query(LoadPlanSequenceSnapshot).filter(LoadPlanSequenceSnapshot.id == payload["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == snapshot.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.sequence.snapshot.generate").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.sequence.snapshot.generated").one()
    assert evidence.evidence_type == "load_plan_sequence_snapshot"
    assert evidence.client_safe is True
    assert audit.target_id == snapshot.id
    assert event.aggregate_id == snapshot.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json


def test_sequence_snapshot_rejects_package_with_empty_load_sequence(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    model.load_sequence_json = "[]"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    error_text = response.json().get("detail", response.json().get("message", ""))
    assert "load sequence" in error_text.lower()


def test_sequence_snapshot_marks_pending_review_item_as_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    codes = [blocker["code"] for blocker in payload["blockers"]]
    assert "REVIEW_ITEM_PENDING" in codes
    assert "decide_review_items" in payload["summary"]["next_actions"]
    assert item["details"]["column_name"] not in json.dumps(payload["blockers"])


def test_sequence_snapshot_uses_latest_review_decision_for_blockers(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic confirmed note"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "NEEDS_MANUAL_ACTION", "decision_note": "Synthetic manual action note"},
        headers=admin_header,
    )
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    codes = [blocker["code"] for blocker in payload["blockers"]]
    assert "REVIEW_ITEM_NEEDS_MANUAL_ACTION" in codes
    assert "REVIEW_ITEM_PENDING" not in codes
    assert "resolve_manual_actions" in payload["summary"]["next_actions"]
    assert "Synthetic manual action note" not in json.dumps(payload)
    assert db_session.query(LoadPlanReviewDecision).count() == 2


def test_sequence_snapshot_confirmed_review_item_does_not_create_review_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    decision = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic confirmation"},
        headers=admin_header,
    )
    assert decision.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    codes = [blocker["code"] for blocker in response.json()["blockers"]]
    assert "REVIEW_ITEM_PENDING" not in codes
    assert "REVIEW_ITEM_REJECTED" not in codes
    assert "REVIEW_ITEM_NEEDS_MANUAL_ACTION" not in codes


def test_sequence_snapshot_rejected_review_item_creates_error_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "REJECTED", "decision_note": "Synthetic rejection"},
        headers=admin_header,
    )
    assert response.status_code == 200

    snapshot = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert snapshot.status_code == 200
    blockers = snapshot.json()["blockers"]
    assert any(item["code"] == "REVIEW_ITEM_REJECTED" and item["severity"] == "ERROR" for item in blockers)
    assert "remove_rejected_items_or_rework_package" in snapshot.json()["summary"]["next_actions"]


def test_sequence_snapshot_excluded_review_item_creates_warning_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "EXCLUDED_FROM_CUTOVER", "decision_note": "Synthetic exclusion"},
        headers=admin_header,
    )
    assert response.status_code == 200

    snapshot = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert snapshot.status_code == 200
    blockers = snapshot.json()["blockers"]
    assert any(
        item["code"] == "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER" and item["severity"] == "WARNING"
        for item in blockers
    )
    assert "review_exclusions" in snapshot.json()["summary"]["next_actions"]


def test_sequence_snapshot_list_detail_and_latest_endpoints(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert created.status_code == 200
    snapshot = created.json()

    listed = client.get("/api/v1/modules/load-plan/sequence/snapshots", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/sequence/snapshots",
        params={"package_id": package["id"], "status": "BLOCKED"},
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/load-plan/sequence/snapshots/{snapshot['id']}",
        headers=admin_header,
    )
    latest = client.get(
        "/api/v1/modules/load-plan/sequence",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert latest.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == snapshot["id"]
    assert detail.json()["id"] == snapshot["id"]
    assert latest.json()["id"] == snapshot["id"]


def test_sequence_latest_endpoint_rejects_missing_snapshot(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/sequence",
        params={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_sequence_snapshot_detail_rejects_missing_snapshot(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/sequence/snapshots/missing_snapshot",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_sequence_snapshot_missing_dictionary_table_creates_blocker(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    model.load_sequence_json = json.dumps(
        [
            {
                "position": 1,
                "table_name": "SYNTHETIC_UNKNOWN_TABLE",
                "row_count": 1,
                "requirement_level": "OPTIONAL",
            }
        ],
        sort_keys=True,
    )
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sequence"][0]["dictionary_table_found"] is False
    assert "DICTIONARY_TABLE_MISSING" in [item["code"] for item in payload["blockers"]]
    assert "review_package_dependencies" in payload["summary"]["next_actions"]
