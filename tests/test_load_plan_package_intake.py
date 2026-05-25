import json
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanPackage
from tests.fixtures_rates import ltl_tl_rate_stack_tables


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic load package batch", "domain_name": "OTM1"},
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


def prepare_approved_exported_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic load package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    return batch, export.json(), approval.json()


def prepare_approved_exported_ltl_tl_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header, scenario_code="LTL_TL_RATE_STACK")
    table_response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={"tables": ltl_tl_rate_stack_tables()},
        headers=admin_header,
    )
    assert table_response.status_code == 200
    validation = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)
    assert validation.status_code == 200
    assert validation.json()["valid"] is True
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic LTL/TL load package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    return batch, export.json(), approval.json()


def prepare_exported_master_data_locations_batch(client, admin_header):
    workbook = Workbook()
    locations = workbook.active
    locations.title = "LOCATIONS"
    locations.append(
        [
            "Location GID",
            "Location XID",
            "Location Name",
            "City",
            "Province Code",
            "Postal Code",
            "Country Code3 GID",
            "Latitude",
            "Longitude",
        ]
    )
    locations.append(
        [
            "OTM1.LOC_SYN_001",
            "LOC_SYN_001",
            "Synthetic Location",
            "Sao Paulo",
            "SP",
            "01000-000",
            "BRA",
            -23.55,
            -46.63,
        ]
    )
    addresses = workbook.create_sheet("LOCATION_ADDRESSES")
    addresses.append(["Location GID", "Line Sequence", "Address Line"])
    addresses.append(["OTM1.LOC_SYN_001", 1, "Synthetic Address Line"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)

    batch_response = client.post(
        "/api/v1/modules/master-data/templates/LOCATIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "locations_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["status"] == "PARSED"

    relationship = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/validate-relationships",
        headers=admin_header,
    )
    assert relationship.status_code == 200
    mapped = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/map",
        headers=admin_header,
    )
    assert mapped.status_code == 200
    output = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-output",
        headers=admin_header,
    )
    assert output.status_code == 200
    csv = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-csv",
        headers=admin_header,
    )
    assert csv.status_code == 200
    export = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/export-csv-package",
        headers=admin_header,
    )
    assert export.status_code == 200
    return batch, export.json()


def test_load_plan_packages_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_packages" in tables


def test_register_rejects_unapproved_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "approved" in response.json()["message"].lower()


def test_register_rejects_approved_rate_batch_without_export(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Approved without export for negative test"},
        headers=admin_header,
    )
    assert approval.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "export" in response.json()["message"].lower()


def test_register_rates_package_creates_load_plan_package(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    package = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload["id"]).one()
    assert payload["source_module"] == "rates"
    assert payload["source_entity_type"] == "rate_batch"
    assert payload["source_entity_id"] == batch["id"]
    assert payload["package_type"] == "rates_csv_zip"
    assert payload["status"] == "REGISTERED"
    assert payload["artifact_id"] == export["artifact_id"]
    assert payload["manifest_id"] == export["manifest_id"]
    assert payload["approval_evidence_id"] == approval["evidence_id"]
    assert payload["load_sequence"] == [
        {
            "position": 6,
            "table_name": "ACCESSORIAL_COST",
            "row_count": 1,
            "requirement_level": "REQUIRED",
        }
    ]
    assert package.created_by == "admin@example.com"
    assert package.registered_at is not None


def test_ltl_tl_rates_package_reaches_zip_analysis_and_cutover_readiness(client, admin_header):
    batch, export, approval = prepare_approved_exported_ltl_tl_rate_batch(client, admin_header)
    package_response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package_response.status_code == 200
    package = package_response.json()

    zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert zip_analysis.status_code == 200
    analysis_payload = zip_analysis.json()
    assert analysis_payload["summary"]["csv_file_count"] == 13
    assert analysis_payload["summary"]["table_count"] == 13
    assert analysis_payload["summary"]["error_count"] == 0
    assert analysis_payload["summary"]["catalog_macro_object_code"] == "RATE_RECORD"

    checklist_response = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    )
    assert checklist_response.status_code == 200
    checklist = checklist_response.json()
    readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    )
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["status"] == "BLOCKED"
    assert readiness_payload["summary"]["latest_zip_analysis_id"] == analysis_payload["id"]
    assert readiness_payload["summary"]["zip_analysis_error_count"] == 0
    rates_family = next(
        item for item in readiness_payload["summary"]["package_families"] if item["family_code"] == "RATES"
    )
    assert rates_family["table_count"] == 13
    assert rates_family["status"] == "BLOCKED"
    assert "OTM1.RO_LTL_TL_001" not in json.dumps(readiness_payload)


def test_ltl_tl_rates_package_flags_child_before_parent_sequence(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_ltl_tl_rate_batch(client, admin_header)
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    ).json()
    model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    sequence = json.loads(model.load_sequence_json)
    cost = next(item for item in sequence if item["table_name"] == "RATE_GEO_COST")
    group = next(item for item in sequence if item["table_name"] == "RATE_GEO_COST_GROUP")
    reordered = [
        item
        for item in sequence
        if item["table_name"] not in {"RATE_GEO_COST", "RATE_GEO_COST_GROUP"}
    ]
    insert_at = next(index for index, item in enumerate(reordered) if item["table_name"] == "RATE_GEO_STOPS") + 1
    reordered[insert_at:insert_at] = [cost, group]
    for index, item in enumerate(reordered, start=1):
        item["position"] = index
    model.load_sequence_json = json.dumps(reordered, sort_keys=True)
    db_session.commit()

    zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert zip_analysis.status_code == 200
    payload = zip_analysis.json()
    assert payload["summary"]["error_count"] == 1
    finding = next(item for item in payload["findings"] if item["code"] == "LOAD_SEQUENCE_PARENT_AFTER_CHILD")
    assert finding["severity"] == "ERROR"
    assert finding["table_name"] == "RATE_GEO_COST"
    assert finding["details"]["parent_table_name"] == "RATE_GEO_COST_GROUP"

    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    ).json()
    assert readiness["status"] == "BLOCKED"
    assert any(blocker["code"] == "ZIP_ANALYSIS_ERROR" for blocker in readiness["blockers"])
    assert "OTM1.RGCG_LTL_TL_001" not in json.dumps(readiness)


def test_load_plan_package_list_and_detail(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/packages", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/packages/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["artifact_id"] == export["artifact_id"]
    assert detail.json()["approval_evidence_id"] == approval["evidence_id"]
    assert detail.json()["summary"]["scenario_code"] == "ACCESSORIAL_ONLY"
    assert "OTM1.ACC_COST_001" not in json.dumps(detail.json())


def test_load_plan_package_list_filters_by_catalog_macro_object(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    ).json()

    matched = client.get(
        "/api/v1/modules/load-plan/packages",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    unmatched = client.get(
        "/api/v1/modules/load-plan/packages",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )

    assert matched.status_code == 200
    assert unmatched.status_code == 200
    assert matched.json()["total"] == 1
    assert matched.json()["items"][0]["id"] == created["id"]
    assert unmatched.json()["total"] == 0
    assert unmatched.json()["items"] == []


def test_load_plan_summary_counts_packages(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get("/api/v1/modules/load-plan/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["registered_packages"] == 1
    assert payload["by_source_module"] == {"rates": 1}
    assert payload["by_status"] == {"REGISTERED": 1}
    assert payload["by_catalog_macro_object"] == {
        "RATE_RECORD": {
            "package_count": 1,
            "catalog_load_plan_path": "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan",
        }
    }
    assert payload["next_actions"] == ["build_csvutil"]


def test_load_plan_module_is_registered(client, admin_header):
    modules = client.get("/api/v1/platform/modules", headers=admin_header)

    assert modules.status_code == 200
    module_ids = [item["id"] for item in modules.json()["items"]]
    assert "load_plan" in module_ids


def test_register_rates_package_creates_client_safe_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").one()
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)

    assert evidence.source_module == "load_plan"
    assert evidence.evidence_type == "load_plan_package_intake"
    assert evidence.client_safe is True
    assert evidence.artifact_id == export["artifact_id"]
    assert evidence.manifest_id == export["manifest_id"]
    assert approval["evidence_id"] in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit_metadata["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert event_payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_register_rates_package_is_idempotent(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    first = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(LoadPlanPackage).count() == 1
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "load_plan_package_intake").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").count() == 1


def test_register_master_data_package_creates_load_plan_package(client, admin_header, db_session):
    batch, export = prepare_exported_master_data_locations_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    package = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload["id"]).one()
    assert payload["source_module"] == "master_data"
    assert payload["source_entity_type"] == "master_data_batch"
    assert payload["source_entity_id"] == batch["batch_id"]
    assert payload["package_type"] == "master_data_csv_zip"
    assert payload["status"] == "REGISTERED"
    assert payload["artifact_id"] == export["artifact_id"]
    assert payload["manifest_id"] == export["manifest_id"]
    assert payload["approval_evidence_id"] is None
    assert payload["load_sequence"] == [
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
    ]
    assert payload["summary"]["catalog_macro_object_code"] == "LOCATION"
    assert payload["summary"]["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/LOCATION/load-plan"
    assert payload["summary"]["template_code"] == "LOCATIONS_BASIC"
    assert package.created_by == "admin@example.com"
    assert package.registered_at is not None


def test_register_master_data_package_creates_client_safe_evidence_audit_and_event(
    client,
    admin_header,
    db_session,
):
    batch, export = prepare_exported_master_data_locations_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_master_data").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").one()
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)

    assert evidence.source_module == "load_plan"
    assert evidence.evidence_type == "load_plan_package_intake"
    assert evidence.client_safe is True
    assert evidence.artifact_id == export["artifact_id"]
    assert evidence.manifest_id == export["manifest_id"]
    assert "OTM1.LOC_SYN_001" not in evidence.summary_json
    assert audit_metadata["catalog_macro_object_code"] == "LOCATION"
    assert event_payload["catalog_macro_object_code"] == "LOCATION"
    assert event_payload["package_type"] == "master_data_csv_zip"
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_register_master_data_package_is_idempotent(client, admin_header, db_session):
    batch, export = prepare_exported_master_data_locations_batch(client, admin_header)

    first = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(LoadPlanPackage).count() == 1
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "load_plan_package_intake").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_master_data").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").count() == 1


def test_load_plan_package_list_filters_master_data_catalog_macro_object(client, admin_header):
    batch, export = prepare_exported_master_data_locations_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    ).json()

    matched = client.get(
        "/api/v1/modules/load-plan/packages",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )

    assert matched.status_code == 200
    assert matched.json()["total"] == 1
    assert matched.json()["items"][0]["id"] == created["id"]
