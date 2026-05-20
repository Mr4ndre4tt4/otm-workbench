import json

from otm_workbench.models import AuditLog, DomainEvent, Evidence
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
