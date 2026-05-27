import json
import zipfile

from otm_workbench.models import Artifact, AuditLog, DomainEvent, Evidence, Manifest
from tests.test_load_plan_csvutil_builder import prepare_registered_load_plan_package
from tests.test_load_plan_cutover_checklist import create_client_safe_evidence


def prepare_ready_checklist_with_csvutil(client, admin_header, db_session):
    _batch, _export, _approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    latest = checklist
    for item in checklist["items"]:
        evidence = create_client_safe_evidence(db_session, checklist["id"], item["table_name"])
        update = client.patch(
            f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
            json={"status": "DONE", "evidence_id": evidence.id},
            headers=admin_header,
        )
        assert update.status_code == 200
        latest = update.json()
    readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    )
    assert readiness.status_code == 200
    csvutil = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist['id']}",
        headers=admin_header,
    )
    assert csvutil.status_code == 200
    return package, latest, readiness.json(), csvutil.json()


def test_cutover_package_export_rejects_missing_checklist_readiness(client, admin_header):
    _batch, _export, _approval, package = prepare_registered_load_plan_package(client, admin_header)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/export-package",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "readiness" in response.json()["message"].lower()


def test_cutover_package_export_creates_client_safe_zip(client, admin_header, db_session):
    package, checklist, readiness, csvutil = prepare_ready_checklist_with_csvutil(
        client,
        admin_header,
        db_session,
    )

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/export-package",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.cutover_package.export").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.cutover_package.exported").one()

    assert payload["status"] == "EXPORTED"
    assert payload["checklist_id"] == checklist["id"]
    assert payload["package_id"] == package["id"]
    assert payload["readiness_status"] == "READY"
    assert payload["csvutil_build_count"] == 1
    assert artifact.artifact_type == "cutover_package_zip"
    assert artifact.content_type == "application/zip"
    assert artifact.project_id == "project_load_plan"
    assert artifact.profile_id == "profile_load_plan"
    assert artifact.environment_id == "env_cutover"
    assert artifact.domain_name == "OTM1"
    assert artifact.visibility == "PROJECT"
    assert manifest.project_id == "project_load_plan"
    assert manifest.profile_id == "profile_load_plan"
    assert manifest.environment_id == "env_cutover"
    assert manifest.domain_name == "OTM1"
    assert manifest.visibility == "PROJECT"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "cutover_package_export"
    assert evidence.project_id == "project_load_plan"
    assert evidence.profile_id == "profile_load_plan"
    assert evidence.environment_id == "env_cutover"
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    assert json.loads(evidence.summary_json)["checklist_id"] == checklist["id"]
    assert json.loads(audit.metadata_json)["checklist_id"] == checklist["id"]
    assert json.loads(event.payload_json)["checklist_id"] == checklist["id"]

    with zipfile.ZipFile(artifact.file_path) as archive:
        names = sorted(archive.namelist())
        manifest_payload = json.loads(archive.read("manifest.json").decode("utf-8"))
        checklist_payload = json.loads(archive.read("checklist.json").decode("utf-8"))
        readiness_payload = json.loads(archive.read("checklist_readiness.json").decode("utf-8"))
        csvutil_payload = json.loads(archive.read("csvutil_builds.json").decode("utf-8"))

    assert names == ["checklist.json", "checklist_readiness.json", "csvutil_builds.json", "manifest.json"]
    assert manifest_payload["manifest_type"] == "cutover_package_export"
    assert manifest_payload["checklist_id"] == checklist["id"]
    assert manifest_payload["readiness_evidence_id"] == readiness["evidence_id"]
    assert checklist_payload["id"] == checklist["id"]
    assert readiness_payload["status"] == "READY"
    assert csvutil_payload["items"][0]["id"] == csvutil["id"]
    assert json.loads(manifest.manifest_json)["manifest_type"] == "cutover_package_export"

    combined = "\n".join(
        [
            json.dumps(payload, sort_keys=True),
            manifest.manifest_json,
            evidence.summary_json,
            audit.metadata_json,
            event.payload_json,
        ]
    )
    assert "OTM1.ACC_COST_001" not in combined
    assert "file_path" not in combined
