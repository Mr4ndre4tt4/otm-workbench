import json
from io import BytesIO

from openpyxl import Workbook

from otm_workbench.models import AuditLog, Job


def create_master_data_parsed_batch(client, admin_header):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_OTM_GUARD", "REGION_OTM_GUARD", "Synthetic Guard Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_OTM_GUARD", "SYN.LOCATION_OTM_GUARD"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)

    response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_otm_guard.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    return response.json()


def create_exported_master_data_batch(client, admin_header):
    batch = create_master_data_parsed_batch(client, admin_header)
    batch_id = batch["batch_id"]
    assert client.post(f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships", headers=admin_header).status_code == 200
    assert client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header).status_code == 200
    assert client.post(f"/api/v1/modules/master-data/batches/{batch_id}/build-output", headers=admin_header).status_code == 200
    assert client.post(f"/api/v1/modules/master-data/batches/{batch_id}/build-csv", headers=admin_header).status_code == 200
    export_response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/export-csv-package",
        headers=admin_header,
    )
    assert export_response.status_code == 200
    return {**batch, "export": export_response.json()}


def test_master_data_otm_import_readiness_requires_existing_batch(client, admin_header):
    response = client.get(
        "/api/v1/modules/master-data/batches/missing-batch/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "MASTER_DATA_BATCH_NOT_FOUND"


def test_master_data_otm_import_readiness_blocks_unexported_batch(client, admin_header):
    batch = create_master_data_parsed_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "BLOCKED"
    assert payload["ready"] is False
    assert any(blocker["code"] == "MASTER_DATA_EXPORT_REQUIRED" for blocker in payload["blockers"])
    assert payload["artifact"] is None


def test_master_data_otm_import_readiness_is_guarded_after_export(client, admin_header):
    batch = create_exported_master_data_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "GUARDED"
    assert payload["ready"] is False
    assert payload["required_capability"] == "master_data.submit_otm"
    assert payload["recommended_transport"] == "CSVUTIL_UPLOAD_OR_INTEGRATION"
    assert payload["artifact"]["content_type"] == "application/zip"
    assert payload["artifact"]["artifact_id"] == batch["export"]["artifact_id"]
    assert {blocker["code"] for blocker in payload["blockers"]} >= {
        "OTM_CONNECTION_NOT_CONFIGURED",
        "OTM_CREDENTIALS_NOT_CONFIGURED",
        "OTM_SUBMIT_CAPABILITY_DISABLED",
    }


def test_submit_master_data_batch_to_otm_is_guarded_and_does_not_create_job(client, admin_header, db_session):
    batch = create_exported_master_data_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "MASTER_DATA_OTM_IMPORT_DISABLED"
    assert payload["details"]["required_capability"] == "master_data.submit_otm"
    assert payload["details"]["readiness_status"] == "GUARDED"
    assert db_session.query(Job).filter(Job.source_module == "master_data").count() == 0
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "master_data.batch.submit_otm.guard")
        .one()
    )
    metadata = json.loads(audit.metadata_json)
    assert metadata["batch_id"] == batch["batch_id"]
    assert metadata["required_capability"] == "master_data.submit_otm"
    assert "OTM_CREDENTIALS_NOT_CONFIGURED" in metadata["blocker_codes"]
    assert "password" not in audit.metadata_json.lower()


def test_submit_master_data_batch_to_otm_rejects_missing_batch(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/batches/missing-batch/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "MASTER_DATA_BATCH_NOT_FOUND"
