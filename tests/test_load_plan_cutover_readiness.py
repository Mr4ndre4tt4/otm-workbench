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
