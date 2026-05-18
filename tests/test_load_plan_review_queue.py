import json
from pathlib import Path
import zipfile

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import Artifact, AuditLog, DomainEvent, LoadPlanReviewItem


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic review queue batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic review queue package"},
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
    rewritten_path = artifact_path.with_suffix(".review-queue.zip")
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


def test_load_plan_review_items_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_review_items" in tables


def test_review_queue_generation_returns_zero_items_for_clean_zip_analysis(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"] == analysis["id"]
    assert payload["package_id"] == package["id"]
    assert payload["created_count"] == 0
    assert payload["existing_count"] == 0
    assert payload["items"] == []
    assert db_session.query(LoadPlanReviewItem).count() == 0


def test_review_queue_generation_creates_item_for_unknown_column(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["created_count"] == 1
    assert payload["existing_count"] == 0
    item = payload["items"][0]
    assert item["source_type"] == "zip_analysis_finding"
    assert item["source_code"] == "CSV_UNKNOWN_COLUMN"
    assert item["severity"] == "ERROR"
    assert item["status"] == "PENDING_REVIEW"
    assert item["category"] == "DATA_DICTIONARY"
    assert item["table_name"] == "ACCESSORIAL_COST"
    assert item["file_name"] == "csv/001_ACCESSORIAL_COST.csv"
    assert item["title"] == "Unknown OTM Data Dictionary column"
    assert item["details"] == {"column_name": "SYNTHETIC_UNKNOWN_COLUMN"}
    assert "DEMO" not in json.dumps(payload)
    assert "OTM1.ACC_COST_001" not in json.dumps(payload)
    assert db_session.query(LoadPlanReviewItem).count() == 1


def test_review_queue_generation_is_idempotent_for_same_analysis(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created_count"] == 1
    assert second.json()["created_count"] == 0
    assert second.json()["existing_count"] == 1
    assert first.json()["items"][0]["id"] == second.json()["items"][0]["id"]
    assert db_session.query(LoadPlanReviewItem).count() == 1


def test_review_queue_generation_creates_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.review_queue.generate_from_zip_analysis").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.review_queue.generated").one()
    assert audit.target_id == analysis["id"]
    assert event.aggregate_id == analysis["id"]
    assert event.status == "PENDING"
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
    assert "DEMO" not in audit.metadata_json
    assert "DEMO" not in event.payload_json


def test_review_queue_list_detail_and_filters(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)
    created = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    ).json()["items"][0]

    listed = client.get("/api/v1/modules/load-plan/review-queue", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/review-queue",
        params={"status": "PENDING_REVIEW", "severity": "ERROR", "package_id": package["id"]},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/review-queue/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert detail.json()["details"] == {"column_name": "SYNTHETIC_UNKNOWN_COLUMN"}


def test_review_queue_generation_rejects_missing_analysis(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/review-queue/from-zip-analysis/missing_analysis",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_review_queue_detail_rejects_missing_item(client, admin_header):
    response = client.get("/api/v1/modules/load-plan/review-queue/missing_item", headers=admin_header)

    assert response.status_code == 404
