import json

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanPackage


def create_registered_locations_package(db_session) -> LoadPlanPackage:
    package = LoadPlanPackage(
        source_module="master_data",
        source_entity_type="master_data_batch",
        source_entity_id="synthetic_locations_batch",
        package_type="master_data_csv_zip",
        status="REGISTERED",
        artifact_id="artifact_locations_csv_zip",
        manifest_id="manifest_locations_csv_zip",
        load_sequence_json=json.dumps(
            [
                {
                    "position": 1,
                    "table_name": "LOCATION",
                    "row_count": 1,
                    "requirement_level": "REQUIRED",
                },
                {
                    "position": 2,
                    "table_name": "LOCATION_ADDRESS",
                    "row_count": 1,
                    "requirement_level": "REQUIRED",
                },
            ],
            sort_keys=True,
        ),
        summary_json=json.dumps(
            {
                "source_module": "master_data",
                "catalog_macro_object_code": "LOCATION",
                "catalog_load_plan_path": "/api/v1/catalog/macro-objects/LOCATION/load-plan",
                "table_count": 2,
                "row_count": 2,
            },
            sort_keys=True,
        ),
        created_by="admin@example.com",
    )
    db_session.add(package)
    db_session.commit()
    return package


def test_cutover_checklist_tables_exist_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "cutover_checklist_templates" in tables
    assert "cutover_checklist_template_items" in tables
    assert "cutover_checklists" in tables
    assert "cutover_checklist_items" in tables


def test_cutover_checklist_template_seed_is_listed(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/cutover-checklists/templates",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    template = payload["items"][0]
    assert template["code"] == "MVP0_STANDARD_CUTOVER"
    assert template["status"] == "PUBLISHED"
    assert template["version"] == 1
    assert [item["item_code"] for item in template["items"]] == [
        "PACKAGE_REGISTERED",
        "SEQUENCE_REVIEW",
        "TABLE_READY",
    ]


def test_create_cutover_checklist_from_load_plan_package(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_id"] == package.id
    assert payload["template_code"] == "MVP0_STANDARD_CUTOVER"
    assert payload["status"] == "DRAFT"
    assert payload["summary"]["catalog_macro_object_code"] == "LOCATION"
    assert payload["summary"]["package_item_count"] == 2
    assert payload["summary"]["table_item_count"] == 2
    assert payload["summary"]["item_count"] == 4
    assert [item["item_code"] for item in payload["items"]] == [
        "PACKAGE_REGISTERED",
        "SEQUENCE_REVIEW",
        "TABLE_READY",
        "TABLE_READY",
    ]
    table_items = [item for item in payload["items"] if item["item_code"] == "TABLE_READY"]
    assert [item["table_name"] for item in table_items] == ["LOCATION", "LOCATION_ADDRESS"]
    assert {item["method"] for item in table_items} == {"CSVUTIL"}
    assert {item["status"] for item in payload["items"]} == {"PENDING"}
    assert "synthetic_locations_batch" not in json.dumps(payload)

    evidence = (
        db_session.query(Evidence)
        .filter(Evidence.source_module == "load_plan")
        .filter(Evidence.evidence_type == "cutover_checklist_created")
        .one()
    )
    assert evidence.client_safe is True
    assert evidence.sensitivity_level == "client_safe"
    assert "synthetic_locations_batch" not in evidence.summary_json

    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "load_plan.cutover_checklist.create_from_package")
        .one()
    )
    assert audit.target_id == payload["id"]
    assert "synthetic_locations_batch" not in audit.metadata_json

    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "load_plan.cutover_checklist.created")
        .one()
    )
    assert event.aggregate_id == payload["id"]
    assert "synthetic_locations_batch" not in event.payload_json


def test_create_cutover_checklist_is_idempotent_for_package(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)

    first = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_get_cutover_checklist_detail(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/load-plan/cutover-checklists/{created['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["package_id"] == package.id
    assert len(payload["items"]) == 4


def test_update_cutover_checklist_item_requires_evidence_for_done(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()
    item = next(item for item in created["items"] if item["item_code"] == "TABLE_READY")

    response = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
        json={"status": "DONE"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "evidence" in response.json()["message"].lower()


def test_update_cutover_checklist_item_status_method_and_evidence(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()
    item = next(item for item in created["items"] if item["table_name"] == "LOCATION")
    evidence = Evidence(
        source_module="load_plan",
        evidence_type="cutover_table_readiness",
        summary_json=json.dumps(
            {
                "source_entity_type": "cutover_checklist_item",
                "checklist_id": created["id"],
                "table_name": "LOCATION",
            },
            sort_keys=True,
        ),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add(evidence)
    db_session.commit()

    response = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
        json={"status": "DONE", "method": "CSVUTIL", "evidence_id": evidence.id},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    updated = next(item for item in payload["items"] if item["table_name"] == "LOCATION")
    assert updated["status"] == "DONE"
    assert updated["method"] == "CSVUTIL"
    assert updated["evidence_id"] == evidence.id
    assert payload["summary"]["status_counts"] == {"DONE": 1, "PENDING": 3}
    assert "synthetic_locations_batch" not in json.dumps(payload)

    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "load_plan.cutover_checklist_item.update")
        .one()
    )
    assert audit.target_id == item["id"]
    assert "synthetic_locations_batch" not in audit.metadata_json

    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "load_plan.cutover_checklist_item.updated")
        .one()
    )
    assert event.aggregate_id == item["id"]
    assert "synthetic_locations_batch" not in event.payload_json


def test_update_cutover_checklist_item_rejects_invalid_status_and_method(
    client,
    admin_header,
    db_session,
):
    package = create_registered_locations_package(db_session)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()
    item = created["items"][0]

    invalid_status = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
        json={"status": "APPROVED"},
        headers=admin_header,
    )
    invalid_method = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
        json={"method": "DIRECT_OTM"},
        headers=admin_header,
    )

    assert invalid_status.status_code == 400
    assert "status" in invalid_status.json()["message"].lower()
    assert invalid_method.status_code == 400
    assert "method" in invalid_method.json()["message"].lower()


def create_client_safe_evidence(db_session, checklist_id: str, table_name: str | None = None) -> Evidence:
    evidence = Evidence(
        source_module="load_plan",
        evidence_type="cutover_table_readiness",
        summary_json=json.dumps(
            {
                "source_entity_type": "cutover_checklist_item",
                "checklist_id": checklist_id,
                "table_name": table_name,
            },
            sort_keys=True,
        ),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add(evidence)
    db_session.commit()
    return evidence


def mark_all_checklist_items_done(client, admin_header, db_session, checklist: dict[str, object]) -> dict[str, object]:
    latest = checklist
    for item in checklist["items"]:
        evidence = create_client_safe_evidence(db_session, str(checklist["id"]), item["table_name"])
        response = client.patch(
            f"/api/v1/modules/load-plan/cutover-checklists/items/{item['id']}",
            json={"status": "DONE", "evidence_id": evidence.id},
            headers=admin_header,
        )
        assert response.status_code == 200
        latest = response.json()
    return latest


def test_cutover_checklist_readiness_reports_blockers(client, admin_header, db_session):
    package = create_registered_locations_package(db_session)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["checklist_id"] == checklist["id"]
    assert payload["package_id"] == package.id
    assert payload["status"] == "BLOCKED"
    assert payload["summary"]["pending_count"] == 4
    assert payload["summary"]["blocked_count"] == 0
    assert payload["summary"]["done_count"] == 0
    assert payload["summary"]["ready"] is False
    assert {blocker["code"] for blocker in payload["blockers"]} == {"REQUIRED_ITEM_PENDING"}
    assert len(payload["blockers"]) == 4
    assert "synthetic_locations_batch" not in json.dumps(payload)

    evidence = (
        db_session.query(Evidence)
        .filter(Evidence.evidence_type == "cutover_checklist_readiness")
        .one()
    )
    assert evidence.client_safe is True
    assert "synthetic_locations_batch" not in evidence.summary_json

    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "load_plan.cutover_checklist.readiness")
        .one()
    )
    assert audit.target_id == checklist["id"]
    assert "synthetic_locations_batch" not in audit.metadata_json

    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "load_plan.cutover_checklist.readiness.generated")
        .one()
    )
    assert event.aggregate_id == checklist["id"]
    assert "synthetic_locations_batch" not in event.payload_json


def test_cutover_checklist_readiness_is_ready_when_required_items_done(
    client,
    admin_header,
    db_session,
):
    package = create_registered_locations_package(db_session)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()
    mark_all_checklist_items_done(client, admin_header, db_session, checklist)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["blockers"] == []
    assert payload["summary"]["ready"] is True
    assert payload["summary"]["done_count"] == 4
    assert payload["summary"]["pending_count"] == 0
    assert payload["summary"]["missing_evidence_count"] == 0


def test_cutover_checklist_readiness_reports_skipped_items_as_review(
    client,
    admin_header,
    db_session,
):
    package = create_registered_locations_package(db_session)
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package.id}",
        headers=admin_header,
    ).json()
    latest = mark_all_checklist_items_done(client, admin_header, db_session, checklist)
    skipped = next(item for item in latest["items"] if item["table_name"] == "LOCATION")
    skipped_response = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{skipped['id']}",
        json={"status": "SKIPPED"},
        headers=admin_header,
    )
    assert skipped_response.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "NEEDS_REVIEW"
    assert payload["summary"]["ready"] is False
    assert payload["summary"]["skipped_count"] == 1
    assert [blocker["code"] for blocker in payload["blockers"]] == ["ITEM_SKIPPED"]
