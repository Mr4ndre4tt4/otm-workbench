import json

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanCutoverHandoff,
    LoadPlanPackage,
    LoadPlanSequenceSnapshot,
)
from tests.test_load_plan_readiness_export import prepare_registered_load_plan_package


def create_package(client, admin_header):
    _batch, _export, _approval, package = prepare_registered_load_plan_package(client, admin_header)
    return package


def create_ready_readiness(client, admin_header, db_session):
    package = create_package(client, admin_header)
    package_model = db_session.query(LoadPlanPackage).filter_by(id=package["id"]).one()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package_model.project_id,
        environment_id=package_model.environment_id,
        profile_id=package_model.profile_id,
        package_id=package["id"],
        status="READY_FOR_REVIEW",
        sequence_json=json.dumps(
            [{"position": 1, "table_name": "ACCESSORIAL_COST", "row_count": 1, "requirement_level": "OPTIONAL"}],
            sort_keys=True,
        ),
        blockers_json="[]",
        summary_json=json.dumps({"blocker_count": 0, "error_count": 0, "warning_count": 0}, sort_keys=True),
        generated_by="admin@example.com",
    )
    db_session.add(snapshot)
    db_session.commit()
    readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert readiness.status_code == 200
    return package, readiness.json()["items"][0]


def export_ready_readiness(client, admin_header, readiness):
    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def archive_readiness_export(client, admin_header):
    response = client.post(
        "/api/v1/evidence-hub/archive-packages",
        json={
            "source_module": "load_plan",
            "evidence_type": "load_plan_readiness_export",
            "status": "CREATED",
            "sensitivity_level": "client_safe",
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_load_plan_cutover_handoffs_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_cutover_handoffs" in tables


def test_cutover_handoff_eligibility_rejects_missing_package(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_cutover_handoff_eligibility_reports_missing_readiness(client, admin_header):
    package = create_package(client, admin_header)

    response = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["eligible"] is False
    assert payload["blockers"][0]["code"] == "CUTOVER_READINESS_MISSING"


def test_cutover_handoff_eligibility_reports_not_ready_readiness(client, admin_header):
    package = create_package(client, admin_header)
    readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert readiness.status_code == 200

    response = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["blockers"][0]["code"] == "CUTOVER_READINESS_NOT_READY"


def test_cutover_handoff_eligibility_reports_missing_export(client, admin_header, db_session):
    package, readiness = create_ready_readiness(client, admin_header, db_session)

    response = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["readiness_id"] == readiness["id"]
    assert response.json()["blockers"][0]["code"] == "READINESS_EXPORT_MISSING"


def test_cutover_handoff_eligibility_reports_missing_archive(client, admin_header, db_session):
    package, readiness = create_ready_readiness(client, admin_header, db_session)
    export_ready_readiness(client, admin_header, readiness)

    response = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["blockers"][0]["code"] == "EVIDENCE_ARCHIVE_MISSING"


def test_cutover_handoff_commit_creates_records_and_transitions_package(
    client,
    admin_header,
    db_session,
):
    package, readiness = create_ready_readiness(client, admin_header, db_session)
    export = export_ready_readiness(client, admin_header, readiness)
    archive = archive_readiness_export(client, admin_header)

    eligibility = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": package["id"]},
        headers=admin_header,
    )
    assert eligibility.status_code == 200
    assert eligibility.json()["eligible"] is True
    assert eligibility.json()["readiness_export_id"] == export["id"]
    assert eligibility.json()["archive_evidence_id"] == archive["evidence_id"]

    response = client.post(
        "/api/v1/modules/load-plan/cutover-handoff",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    handoff = db_session.query(LoadPlanCutoverHandoff).filter_by(id=payload["id"]).one()
    package_row = db_session.query(LoadPlanPackage).filter_by(id=package["id"]).one()
    evidence = db_session.query(Evidence).filter_by(id=handoff.evidence_id).one()
    audit = db_session.query(AuditLog).filter_by(action="load_plan.cutover_handoff.commit").one()
    event = db_session.query(DomainEvent).filter_by(event_type="load_plan.cutover_handoff.committed").one()
    assert payload["status"] == "READY_FOR_CUTOVER"
    assert payload["summary"]["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        payload["summary"]["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert package_row.status == "READY_FOR_CUTOVER"
    assert evidence.evidence_type == "load_plan_cutover_handoff"
    assert evidence.client_safe is True
    handoff_summary = json.loads(handoff.summary_json)
    evidence_summary = json.loads(evidence.summary_json)
    assert handoff_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert evidence_summary["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        evidence_summary["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert audit.target_id == handoff.id
    assert event.aggregate_id == handoff.id

    combined = "\n".join([handoff.summary_json, evidence.summary_json, audit.metadata_json, event.payload_json])
    assert "OTM1.ACC_COST_001" not in combined
    assert "Reviewed for synthetic readiness export" not in combined
    assert "file_path" not in combined


def test_cutover_handoff_commit_rejects_ineligible_package(client, admin_header):
    package = create_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-handoff",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "CUTOVER_READINESS_MISSING" in response.json()["message"]


def test_cutover_handoff_commit_is_idempotent_and_list_detail_work(client, admin_header, db_session):
    package, readiness = create_ready_readiness(client, admin_header, db_session)
    export_ready_readiness(client, admin_header, readiness)
    archive_readiness_export(client, admin_header)

    first = client.post(
        "/api/v1/modules/load-plan/cutover-handoff",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    second = client.post(
        "/api/v1/modules/load-plan/cutover-handoff",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    listed = client.get(
        "/api/v1/modules/load-plan/cutover-handoff",
        params={"package_id": package["id"], "status": "READY_FOR_CUTOVER"},
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/load-plan/cutover-handoff/{first.json()['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert detail.status_code == 200
    assert detail.json()["id"] == first.json()["id"]
