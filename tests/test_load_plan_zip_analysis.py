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
    LoadPlanZipAnalysis,
    Manifest,
)


def test_load_plan_zip_analyses_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_zip_analyses" in tables


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic ZIP analysis batch", "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001", extra_fields=None):
    row = {
        "ACCESSORIAL_COST_GID": f"OTM1.{xid}",
        "ACCESSORIAL_COST_XID": xid,
    }
    if extra_fields:
        row.update(extra_fields)
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={"tables": [{"table_name": "ACCESSORIAL_COST", "rows": [row]}]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def prepare_registered_load_plan_package(client, admin_header, extra_fields=None):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"], extra_fields=extra_fields)
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic ZIP analysis package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def test_zip_analysis_succeeds_for_registered_package(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    analysis = db_session.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == payload["id"]).one()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "ANALYZED"
    assert payload["source_artifact_id"] == export["artifact_id"]
    assert payload["source_manifest_id"] == export["manifest_id"]
    assert payload["summary"]["csv_file_count"] == 1
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        payload["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["warning_count"] == 0
    assert payload["findings"] == []
    assert analysis.created_by == "admin@example.com"
    assert analysis.analyzed_at is not None


def test_zip_analysis_creates_manifest_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.zip_analysis.run").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.zip_analysis.completed").one()
    manifest_json = json.loads(manifest.manifest_json)

    assert manifest_json["manifest_type"] == "zip_analysis"
    assert manifest_json["package"]["id"] == package["id"]
    assert manifest_json["package"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert manifest_json["files"][0]["table_name"] == "ACCESSORIAL_COST"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "load_plan_zip_analysis"
    assert evidence.artifact_id == export["artifact_id"]
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
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_zip_analysis_accepts_csvutil_reference_package_shape(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".csvutil_reference_shape.zip")
    csv_payload = (
        "ACCESSORIAL_COST\n"
        "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID\n"
        "OTM1.SYNTH_ACC_COST_001,SYNTH_ACC_COST_001\n"
    ).encode("utf-8")
    with zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as rewritten:
        rewritten.writestr(
            "csvutil.ctl",
            "-dataFileName 001_ACCESSORIAL_COST.csv -command xcsv -tableName ACCESSORIAL_COST\n",
        )
        rewritten.writestr(
            "export/csvutil.ctl",
            "-dataFileName 001_ACCESSORIAL_COST.csv -command ii\n",
        )
        rewritten.writestr("export/001_ACCESSORIAL_COST.csv", csv_payload)
        rewritten.writestr("__MACOSX/._001_ACCESSORIAL_COST.csv", b"apple metadata")
        rewritten.writestr("export/.DS_Store", b"apple metadata")
        rewritten.writestr("export/export.zip.result.zip", b"synthetic nested result")
    artifact.file_path = str(rewritten_path)
    artifact.file_name = rewritten_path.name
    artifact.size_bytes = rewritten_path.stat().st_size
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["csv_file_count"] == 1
    assert payload["summary"]["ctl_file_count"] == 2
    assert payload["summary"]["ignored_file_count"] == 2
    assert payload["summary"]["nested_result_zip_count"] == 1
    assert payload["summary"]["ctl_command_modes"] == ["ii", "xcsv"]
    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["warning_count"] == 0
    assert payload["findings"] == []
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    manifest_json = json.loads(manifest.manifest_json)
    assert manifest_json["files"][0]["file_name"] == "export/001_ACCESSORIAL_COST.csv"
    assert manifest_json["ignored_files"] == ["__MACOSX/._001_ACCESSORIAL_COST.csv", "export/.DS_Store"]
    assert "SYNTH_ACC_COST_001" not in json.dumps(payload)
    assert "SYNTH_ACC_COST_001" not in manifest.manifest_json


def test_zip_analysis_flags_ctl_missing_csv_and_table_mismatch(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".csvutil_ctl_mismatch.zip")
    with zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as rewritten:
        rewritten.writestr(
            "csvutil.ctl",
            "\n".join(
                [
                    "-dataFileName 001_ACCESSORIAL_COST.csv -command xcsv -tableName RATE_GEO",
                    "-dataFileName 999_MISSING_TABLE.csv -command xcsv -tableName RATE_OFFERING",
                ]
            )
            + "\n",
        )
        rewritten.writestr(
            "export/csvutil.ctl",
            "-dataFileName 001_ACCESSORIAL_COST.csv -command ii\n",
        )
        rewritten.writestr(
            "export/001_ACCESSORIAL_COST.csv",
            (
                "ACCESSORIAL_COST\n"
                "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID\n"
                "OTM1.SYNTH_ACC_COST_001,SYNTH_ACC_COST_001\n"
            ),
        )
    artifact.file_path = str(rewritten_path)
    artifact.file_name = rewritten_path.name
    artifact.size_bytes = rewritten_path.stat().st_size
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    codes = [item["code"] for item in payload["findings"]]
    assert "CSVUTIL_CTL_REFERENCED_CSV_MISSING" in codes
    assert "CSVUTIL_CTL_TABLE_MISMATCH" in codes
    missing = next(item for item in payload["findings"] if item["code"] == "CSVUTIL_CTL_REFERENCED_CSV_MISSING")
    mismatch = next(item for item in payload["findings"] if item["code"] == "CSVUTIL_CTL_TABLE_MISMATCH")
    assert missing["file_name"] == "csvutil.ctl"
    assert missing["details"]["data_file_name"] == "999_MISSING_TABLE.csv"
    assert mismatch["file_name"] == "csvutil.ctl"
    assert mismatch["table_name"] == "ACCESSORIAL_COST"
    assert mismatch["details"]["ctl_table_name"] == "RATE_GEO"
    assert mismatch["details"]["csv_file_name"] == "export/001_ACCESSORIAL_COST.csv"
    assert "SYNTH_ACC_COST_001" not in json.dumps(payload)


def test_zip_analysis_sanitizes_ctl_mail_notification_options(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".csvutil_mail_options.zip")
    with zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as rewritten:
        rewritten.writestr(
            "csvutil.ctl",
            (
                "-dataFileName 001_ACCESSORIAL_COST.csv -command xcsv "
                "-tableName ACCESSORIAL_COST -mailTo ops@example.test "
                "-mailFrom loader@example.test -mailSubject Synthetic Load\n"
            ),
        )
        rewritten.writestr(
            "export/001_ACCESSORIAL_COST.csv",
            (
                "ACCESSORIAL_COST\n"
                "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID\n"
                "OTM1.SYNTH_ACC_COST_001,SYNTH_ACC_COST_001\n"
            ),
        )
    artifact.file_path = str(rewritten_path)
    artifact.file_name = rewritten_path.name
    artifact.size_bytes = rewritten_path.stat().st_size
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["ctl_mail_option_count"] == 3
    assert payload["summary"]["ctl_has_mail_options"] is True
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    manifest_json = json.loads(manifest.manifest_json)
    assert manifest_json["ctl_mail_options"] == [
        {"file_name": "csvutil.ctl", "option": "mailFrom"},
        {"file_name": "csvutil.ctl", "option": "mailSubject"},
        {"file_name": "csvutil.ctl", "option": "mailTo"},
    ]
    response_text = json.dumps(payload)
    assert "ops@example.test" not in response_text
    assert "loader@example.test" not in response_text
    assert "Synthetic Load" not in response_text
    assert "ops@example.test" not in manifest.manifest_json
    assert "loader@example.test" not in manifest.manifest_json
    assert "Synthetic Load" not in manifest.manifest_json
    assert "SYNTH_ACC_COST_001" not in response_text


def test_zip_analysis_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/zip-analysis", headers=admin_header)
    catalog_matched = client.get(
        "/api/v1/modules/load-plan/zip-analysis",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/load-plan/zip-analysis",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/zip-analysis/{created['id']}", headers=admin_header)

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
    assert catalog_unmatched.json()["code"] == "UNSUPPORTED_CATALOG_MACRO_OBJECT"
    assert catalog_unmatched.json()["message"] == "Catalog macro-object is outside the Load Plan package scope."
    assert catalog_unmatched.json()["details"] == {"catalog_macro_object_code": "LOCATION"}
    assert catalog_unmatched.json()["catalog_macro_object_code"] == "LOCATION"
    assert detail.json()["summary"]["package_type"] == "rates_csv_zip"


def test_zip_analysis_requires_alter_session_for_date_columns(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(
        client,
        admin_header,
        extra_fields={"EFFECTIVE_DATE": "2026-05-18 00:00:00"},
    )

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()["findings"]]
    assert "CSV_DATE_ALTER_SESSION_MISSING" not in codes


def test_zip_analysis_flags_unknown_columns(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".rewritten.zip")
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

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    findings = response.json()["findings"]
    assert any(item["code"] == "CSV_UNKNOWN_COLUMN" for item in findings)
    assert "DEMO" not in json.dumps(response.json())


def test_zip_analysis_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_zip_analysis_rejects_missing_source_artifact(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = "missing_artifact"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "artifact" in response.json()["message"].lower()


def test_zip_analysis_rejects_non_zip_artifact(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    text_path = Path("var/artifacts/test-fixtures/not_a_zip.txt")
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text("synthetic text artifact", encoding="utf-8")
    artifact = Artifact(
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path=str(text_path),
        file_name=text_path.name,
        content_type="text/plain",
        sha256="synthetic",
        size_bytes=text_path.stat().st_size,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = artifact.id
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "readable zip" in response.json()["message"].lower()
