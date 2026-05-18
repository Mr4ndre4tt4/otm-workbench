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
    assert build.created_by == "admin@example.com"
    assert build.built_at is not None
