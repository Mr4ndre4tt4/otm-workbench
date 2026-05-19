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
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic review decision batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic review decision package"},
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
    rewritten_path = artifact_path.with_suffix(".review-decisions.zip")
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


def create_review_item(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert analysis.status_code == 200
    review = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis.json()['id']}",
        headers=admin_header,
    )
    assert review.status_code == 200
    return package, analysis.json(), review.json()["items"][0]


def test_load_plan_review_decisions_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_review_decisions" in tables


def test_review_decision_updates_item_and_creates_evidence_audit_event(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic check accepted by reviewer"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_item_id"] == item["id"]
    assert payload["package_id"] == package["id"]
    assert payload["decision_status"] == "CONFIRMED"
    assert payload["decision_note"] == "Synthetic check accepted by reviewer"
    assert payload["decided_by"] == "admin@example.com"
    assert payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    updated_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    decision = db_session.query(LoadPlanReviewDecision).filter(LoadPlanReviewDecision.id == payload["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == decision.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.review_queue.decide").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.review_queue.decided").one()
    summary = json.loads(evidence.summary_json)
    assert updated_item.status == "CONFIRMED"
    assert evidence.evidence_type == "load_plan_review_decision"
    assert evidence.client_safe is True
    assert summary["decision_status"] == "CONFIRMED"
    assert summary["decision_note_present"] is True
    assert summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert summary["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert audit.target_id == item["id"]
    assert event.aggregate_id == item["id"]
    assert "Synthetic check accepted by reviewer" not in audit.metadata_json
    assert "Synthetic check accepted by reviewer" not in event.payload_json


def test_review_queue_list_and_detail_include_latest_decision(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    decision = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "NEEDS_MANUAL_ACTION", "decision_note": ""},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/review-queue", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/review-queue/{item['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    listed_item = listed.json()["items"][0]
    assert listed_item["latest_decision_id"] == decision["id"]
    assert listed_item["latest_decision_status"] == "NEEDS_MANUAL_ACTION"
    assert listed_item["latest_decided_at"] == decision["decided_at"]
    assert detail.json()["latest_decision_id"] == decision["id"]
    assert detail.json()["latest_decision_status"] == "NEEDS_MANUAL_ACTION"


def test_review_decision_rejects_invalid_status_without_changing_item(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "APPROVED_FOR_LOAD", "decision_note": "Invalid synthetic status"},
        headers=admin_header,
    )

    assert response.status_code == 400
    updated_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    assert updated_item.status == "PENDING_REVIEW"
    assert db_session.query(LoadPlanReviewDecision).count() == 0


def test_review_decision_rejects_missing_item(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/review-queue/missing_item/decide",
        json={"decision_status": "CONFIRMED", "decision_note": ""},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_review_decision_records_history_when_item_is_decided_again(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "REJECTED", "decision_note": "First synthetic review"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "EXCLUDED_FROM_CUTOVER", "decision_note": "Second synthetic review"},
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert db_session.query(LoadPlanReviewDecision).count() == 2
    updated_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    assert updated_item.status == "EXCLUDED_FROM_CUTOVER"
    detail = client.get(f"/api/v1/modules/load-plan/review-queue/{item['id']}", headers=admin_header)
    assert detail.json()["latest_decision_id"] == second.json()["id"]
    assert detail.json()["latest_decision_status"] == "EXCLUDED_FROM_CUTOVER"


def test_review_decision_evidence_tracks_note_presence_without_copying_note(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    note = "Do not copy this synthetic note into client-safe metadata"

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": note},
        headers=admin_header,
    )

    assert response.status_code == 200
    decision = db_session.query(LoadPlanReviewDecision).filter(LoadPlanReviewDecision.id == response.json()["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == decision.evidence_id).one()
    summary = json.loads(evidence.summary_json)
    assert summary["decision_note_present"] is True
    assert note not in evidence.summary_json
