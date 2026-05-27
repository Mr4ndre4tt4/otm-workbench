import json

from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanZipAnalysis
from tests.test_load_plan_cutover_package_export import prepare_ready_checklist_with_csvutil


def test_cutover_go_no_go_returns_no_go_without_export_package(client, admin_header, db_session):
    package, checklist, readiness, _csvutil = prepare_ready_checklist_with_csvutil(
        client,
        admin_header,
        db_session,
    )

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/go-no-go",
        json={"decision_note": "Synthetic operational review."},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()

    assert payload["decision"] == "NO_GO"
    assert payload["checklist_id"] == checklist["id"]
    assert payload["package_id"] == package["id"]
    assert payload["readiness_status"] == "READY"
    assert payload["readiness_evidence_id"] == readiness["evidence_id"]
    assert payload["cutover_package_evidence_id"] is None
    assert payload["blockers"][0]["code"] == "CUTOVER_PACKAGE_EXPORT_MISSING"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "cutover_go_no_go_decision"
    assert evidence.project_id == "project_load_plan"
    assert evidence.profile_id == "profile_load_plan"
    assert evidence.environment_id == "env_cutover"
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    assert json.loads(evidence.summary_json)["decision"] == "NO_GO"


def test_cutover_go_no_go_returns_go_after_export_package(client, admin_header, db_session):
    package, checklist, readiness, _csvutil = prepare_ready_checklist_with_csvutil(
        client,
        admin_header,
        db_session,
    )
    export = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/export-package",
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/go-no-go",
        json={"decision_note": "Synthetic operational review."},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.cutover_go_no_go.decide").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.cutover_go_no_go.decided").one()

    assert payload["decision"] == "GO"
    assert payload["checklist_id"] == checklist["id"]
    assert payload["package_id"] == package["id"]
    assert payload["readiness_status"] == "READY"
    assert payload["readiness_evidence_id"] == readiness["evidence_id"]
    assert payload["cutover_package_evidence_id"] == export["evidence_id"]
    assert payload["blockers"] == []
    assert evidence.client_safe is True
    assert evidence.project_id == "project_load_plan"
    assert evidence.profile_id == "profile_load_plan"
    assert evidence.environment_id == "env_cutover"
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    assert json.loads(evidence.summary_json)["decision"] == "GO"
    assert json.loads(audit.metadata_json)["cutover_package_evidence_id"] == export["evidence_id"]
    assert json.loads(event.payload_json)["decision"] == "GO"

    combined = "\n".join(
        [
            json.dumps(payload, sort_keys=True),
            evidence.summary_json,
            audit.metadata_json,
            event.payload_json,
        ]
    )
    assert "OTM1.ACC_COST_001" not in combined
    assert "Synthetic operational review." not in combined


def test_cutover_go_no_go_rechecks_zip_analysis_after_ready_evidence(client, admin_header, db_session):
    package, checklist, readiness, _csvutil = prepare_ready_checklist_with_csvutil(
        client,
        admin_header,
        db_session,
    )
    export = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/export-package",
        headers=admin_header,
    ).json()
    analysis = LoadPlanZipAnalysis(
        package_id=package["id"],
        status="ANALYZED",
        source_artifact_id=package["artifact_id"],
        source_manifest_id=package["manifest_id"],
        summary_json=json.dumps(
            {"package_id": package["id"], "error_count": 1, "warning_count": 0, "finding_count": 1},
            sort_keys=True,
        ),
        findings_json=json.dumps(
            [
                {
                    "severity": "ERROR",
                    "code": "CSVUTIL_CTL_REFERENCED_CSV_MISSING",
                    "message": "CSVUTIL CTL references a missing CSV file.",
                    "table_name": None,
                    "file_name": "csvutil.ctl",
                    "details": {"data_file_name": "999_MISSING_TABLE.csv"},
                }
            ],
            sort_keys=True,
        ),
        created_by="admin@example.com",
    )
    db_session.add(analysis)
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/go-no-go",
        json={"decision_note": "Synthetic operational review."},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "NO_GO"
    assert payload["readiness_status"] == "BLOCKED"
    assert payload["readiness_evidence_id"] == readiness["evidence_id"]
    assert payload["cutover_package_evidence_id"] == export["evidence_id"]
    assert any(blocker["code"] == "ZIP_ANALYSIS_ERROR" for blocker in payload["blockers"])
    assert payload["live_readiness_summary"]["latest_zip_analysis_id"] == analysis.id
    combined = json.dumps(payload, sort_keys=True)
    assert "999_MISSING_TABLE.csv" in combined
    assert "OTM1.ACC_COST_001" not in combined
    assert "Synthetic operational review." not in combined
