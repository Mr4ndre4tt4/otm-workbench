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
