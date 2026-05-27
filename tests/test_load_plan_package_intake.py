import json
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanCutoverHandoff,
    LoadPlanPackage,
    LoadPlanReviewItem,
)
from tests.fixtures_rates import ltl_tl_rate_stack_tables


def create_rate_batch(
    client,
    admin_header,
    scenario_code="ACCESSORIAL_ONLY",
    *,
    project_id=None,
    environment_id=None,
    domain_name="OTM1",
):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": scenario_code,
            "name": "Synthetic load package batch",
            "domain_name": domain_name,
            "project_id": project_id,
            "environment_id": environment_id,
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001", domain_name="OTM1"):
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": f"{domain_name}.{xid}",
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


def prepare_approved_exported_rate_batch(
    client,
    admin_header,
    *,
    project_id=None,
    environment_id=None,
    domain_name="OTM1",
):
    batch = create_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name=domain_name,
    )
    add_accessorial_table(client, admin_header, batch["id"], domain_name=domain_name)
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


def create_project_environment(client, admin_header, *, name_suffix=""):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"Synthetic Load Plan Workspace{name_suffix}"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"Synthetic Load Plan Project{name_suffix}"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    return project["id"], environment["id"]


def set_active_context(
    client,
    admin_header,
    *,
    project_id,
    environment_id,
    domain_name,
    can_view_all_domains=False,
):
    response = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project_id,
            "environment_id": environment_id,
            "domain_name": domain_name,
            "can_view_all_domains": can_view_all_domains,
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


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


def create_master_data_template_from_scenario_pack(client, admin_header, pack_code):
    packs = client.get("/api/v1/modules/master-data/scenario-packs", headers=admin_header).json()["items"]
    draft_payload = next(pack["draft_payload"] for pack in packs if pack["code"] == pack_code)
    draft = client.post(
        "/api/v1/modules/master-data/templates/drafts",
        json=draft_payload,
        headers=admin_header,
    )
    assert draft.status_code == 200
    publish = client.post(
        f"/api/v1/modules/master-data/templates/{draft_payload['code']}/publish",
        headers=admin_header,
    )
    assert publish.status_code == 200
    assert publish.json()["validation"]["valid"] is True
    return draft_payload["code"]


def operational_locations_editor_payload() -> dict[str, object]:
    return {
        "file_name": "locations_operational_load_plan.xlsx",
        "sheets": [
            {
                "sheet_code": "LOCATIONS",
                "rows": [
                    {
                        "row_id": "LOCATIONS-1",
                        "values": {
                            "location_gid": "SYN.LOC_DC_001",
                            "location_xid": "LOC_DC_001",
                            "location_name": "Synthetic Distribution Center",
                            "city": "Atlanta",
                            "province_code": "GA",
                            "postal_code": "30301",
                            "country_code3_gid": "USA",
                            "time_zone_gid": "America/New_York",
                            "lat": "33.74900",
                            "lon": "-84.38800",
                            "location_equipment_group_profile_gid": "SYN.EGP_DRYVAN",
                            "appointment_activity_type": "LIVE",
                        },
                    }
                ],
            },
            {
                "sheet_code": "LOCATION_ADDRESSES",
                "rows": [
                    {
                        "row_id": "LOCATION_ADDRESSES-1",
                        "values": {
                            "address_location_gid": "SYN.LOC_DC_001",
                            "address_line_sequence": "1",
                            "address_line": "100 Synthetic Logistics Way",
                        },
                    }
                ],
            },
            {
                "sheet_code": "LOCATION_CAPACITIES",
                "rows": [
                    {
                        "row_id": "LOCATION_CAPACITIES-1",
                        "values": {
                            "capacity_location_gid": "SYN.LOC_DC_001",
                            "location_capacity_gid": "SYN.LOC_CAP_DC_001",
                            "location_capacity_xid": "LOC_CAP_DC_001",
                            "capacity_calendar_gid": "SYN.CAL_DOCK_WEEKDAY",
                        },
                    }
                ],
            },
            {
                "sheet_code": "LOCATION_ACTIVITY_TIMES",
                "rows": [
                    {
                        "row_id": "LOCATION_ACTIVITY_TIMES-1",
                        "values": {
                            "activity_location_gid": "SYN.LOC_DC_001",
                            "location_role_gid": "SYN.LOC_ROLE_SHIPPER",
                            "activity_time_def_gid": "SYN.ACT_TIME_LIVE_90",
                        },
                    }
                ],
            },
            {
                "sheet_code": "LOCATION_DOCKS",
                "rows": [
                    {
                        "row_id": "LOCATION_DOCKS-1",
                        "values": {
                            "dock_location_gid": "SYN.LOC_DC_001",
                            "load_unload_point": "DOCK_A",
                            "dock_equipment_group_profile_gid": "SYN.EGP_DRYVAN",
                            "is_load": "Y",
                            "load_sequence": "10",
                            "is_unload": "Y",
                            "unload_sequence": "10",
                        },
                    }
                ],
            },
            {
                "sheet_code": "EQUIPMENT_PROFILES",
                "rows": [
                    {
                        "row_id": "EQUIPMENT_PROFILES-1",
                        "values": {
                            "equipment_group_profile_gid": "SYN.EGP_DRYVAN",
                            "equipment_group_profile_xid": "EGP_DRYVAN",
                            "equipment_group_profile_name": "Synthetic Dry Van Equipment",
                        },
                    }
                ],
            },
            {
                "sheet_code": "EQUIPMENT_PROFILE_DETAILS",
                "rows": [
                    {
                        "row_id": "EQUIPMENT_PROFILE_DETAILS-1",
                        "values": {
                            "detail_equipment_group_profile_gid": "SYN.EGP_DRYVAN",
                            "equipment_group_gid": "SYN.EQG_53_DRYVAN",
                        },
                    }
                ],
            },
        ],
    }


def prepare_exported_operational_locations_batch(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "LOCATION_OPERATIONAL")
    editor_payload = operational_locations_editor_payload()
    batch_response = client.post(
        f"/api/v1/modules/master-data/templates/{template_code}/workbook-editor/batches",
        json=editor_payload,
        headers=admin_header,
    )
    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["status"] == "PARSED"
    relationship = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/validate-relationships",
        headers=admin_header,
    )
    assert relationship.status_code == 200
    assert relationship.json()["status"] == "RELATIONSHIP_VALIDATED", relationship.json()
    assert client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/map", headers=admin_header).status_code == 200
    assert client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-output", headers=admin_header).status_code == 200
    csv = client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-csv", headers=admin_header)
    assert csv.status_code == 200
    assert {item["table_name"] for item in csv.json()["files"]} == {
        "LOCATION",
        "LOCATION_ADDRESS",
        "LOCATION_CAPACITY",
        "LOCATION_ACTIVITY_TIME_DEF",
        "LOCATION_LOAD_UNLOAD_POINT",
        "EQUIPMENT_GROUP_PROFILE",
        "EQUIPMENT_GROUP_PROFILE_D",
    }
    export = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/export-csv-package",
        headers=admin_header,
    )
    assert export.status_code == 200
    return batch, export.json()


def create_operational_locations_batch_with_missing_location_parent(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "LOCATION_OPERATIONAL")
    editor_payload = operational_locations_editor_payload()
    dock_rows = next(sheet["rows"] for sheet in editor_payload["sheets"] if sheet["sheet_code"] == "LOCATION_DOCKS")
    dock_rows[0]["values"]["dock_location_gid"] = "SYN.LOC_MISSING_001"
    return client.post(
        f"/api/v1/modules/master-data/templates/{template_code}/workbook-editor/batches",
        json=editor_payload,
        headers=admin_header,
    )


def item_packaging_editor_payload() -> dict[str, object]:
    return {
        "file_name": "item_packaging_load_plan.xlsx",
        "sheets": [
            {
                "sheet_code": "ITEMS",
                "rows": [
                    {
                        "row_id": "ITEMS-1",
                        "values": {
                            "item_gid": "SYN.ITEM_WIDGET_001",
                            "item_xid": "ITEM_WIDGET_001",
                            "item_name": "Synthetic Widget",
                            "item_type_gid": "SYN.ITEM_TYPE_GENERAL",
                            "unit_of_measure": "EA",
                        },
                    }
                ],
            },
            {
                "sheet_code": "SHIP_UNIT_SPECS",
                "rows": [
                    {
                        "row_id": "SHIP_UNIT_SPECS-1",
                        "values": {
                            "ship_unit_spec_gid": "SYN.SUS_CASE",
                            "ship_unit_spec_xid": "SUS_CASE",
                            "ship_unit_spec_name": "Synthetic Case",
                            "unit_type": "P",
                            "length": "12",
                            "length_uom_code": "IN",
                            "width": "10",
                            "width_uom_code": "IN",
                            "height": "8",
                            "height_uom_code": "IN",
                            "tare_weight": "1.5",
                            "tare_weight_uom_code": "LB",
                            "effective_volume": "0.55",
                            "effective_volume_uom_code": "CUFT",
                            "is_in_on_max": "I",
                        },
                    },
                    {
                        "row_id": "SHIP_UNIT_SPECS-2",
                        "values": {
                            "ship_unit_spec_gid": "SYN.SUS_PALLET",
                            "ship_unit_spec_xid": "SUS_PALLET",
                            "ship_unit_spec_name": "Synthetic Pallet",
                            "unit_type": "T",
                            "length": "48",
                            "length_uom_code": "IN",
                            "width": "40",
                            "width_uom_code": "IN",
                            "height": "60",
                            "height_uom_code": "IN",
                            "tare_weight": "45",
                            "tare_weight_uom_code": "LB",
                            "effective_volume": "66.67",
                            "effective_volume_uom_code": "CUFT",
                            "is_in_on_max": "O",
                        },
                    },
                ],
            },
            {
                "sheet_code": "PACKAGED_ITEMS",
                "rows": [
                    {
                        "row_id": "PACKAGED_ITEMS-1",
                        "values": {
                            "packaged_item_gid": "SYN.PKG_WIDGET_CASE",
                            "packaged_item_xid": "PKG_WIDGET_CASE",
                            "package_item_gid": "SYN.ITEM_WIDGET_001",
                            "packaging_unit_gid": "SYN.SUS_CASE",
                            "package_ship_unit_weight": "24",
                            "package_ship_unit_weight_uom": "LB",
                            "package_su_volume": "0.55",
                            "package_su_volume_uom_code": "CUFT",
                            "package_su_length": "12",
                            "package_su_length_uom_code": "IN",
                            "package_su_width": "10",
                            "package_su_width_uom_code": "IN",
                            "package_su_height": "8",
                            "package_su_height_uom_code": "IN",
                        },
                    }
                ],
            },
            {
                "sheet_code": "TI_HI",
                "rows": [
                    {
                        "row_id": "TI_HI-1",
                        "values": {
                            "tihi_sequence_no": "10",
                            "tihi_packaged_item_gid": "SYN.PKG_WIDGET_CASE",
                            "tihi_packaging_unit_gid": "SYN.SUS_CASE",
                            "transport_handling_unit_gid": "SYN.SUS_PALLET",
                            "num_layers": "4",
                            "quantity_per_layer": "6",
                        },
                    }
                ],
            },
        ],
    }


def prepare_exported_item_packaging_batch(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "ITEM_PACKAGING_OPERATIONAL")
    editor_payload = item_packaging_editor_payload()
    batch_response = client.post(
        f"/api/v1/modules/master-data/templates/{template_code}/workbook-editor/batches",
        json=editor_payload,
        headers=admin_header,
    )
    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["status"] == "PARSED"
    relationship = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/validate-relationships",
        headers=admin_header,
    )
    assert relationship.status_code == 200
    assert relationship.json()["status"] == "RELATIONSHIP_VALIDATED", relationship.json()
    assert client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/map", headers=admin_header).status_code == 200
    assert client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-output", headers=admin_header).status_code == 200
    csv = client.post(f"/api/v1/modules/master-data/batches/{batch['batch_id']}/build-csv", headers=admin_header)
    assert csv.status_code == 200
    assert [item["table_name"] for item in csv.json()["files"]] == ["ITEM", "SHIP_UNIT_SPEC", "PACKAGED_ITEM", "TI_HI"]
    export = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/export-csv-package",
        headers=admin_header,
    )
    assert export.status_code == 200
    return batch, export.json()


def create_item_packaging_batch_with_missing_transport_unit_parent(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "ITEM_PACKAGING_OPERATIONAL")
    editor_payload = item_packaging_editor_payload()
    tihi_rows = next(sheet["rows"] for sheet in editor_payload["sheets"] if sheet["sheet_code"] == "TI_HI")
    tihi_rows[0]["values"]["transport_handling_unit_gid"] = "SYN.SUS_MISSING_PALLET"
    return client.post(
        f"/api/v1/modules/master-data/templates/{template_code}/workbook-editor/batches",
        json=editor_payload,
        headers=admin_header,
    )


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


def test_load_plan_package_list_and_detail_follow_active_context_scope(client, admin_header, db_session):
    project_id, environment_id = create_project_environment(client, admin_header)
    other_project_id, other_environment_id = create_project_environment(client, admin_header, name_suffix=" Other")
    visible_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    hidden_domain_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    hidden_environment_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id="env_dev",
        domain_name="OTM1",
    )
    hidden_project_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=other_project_id,
        environment_id=other_environment_id,
        domain_name="OTM1",
    )
    visible = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{visible_batch['id']}",
        headers=admin_header,
    ).json()
    hidden_domain = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{hidden_domain_batch['id']}",
        headers=admin_header,
    ).json()
    client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{hidden_environment_batch['id']}",
        headers=admin_header,
    )
    hidden_project = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{hidden_project_batch['id']}",
        headers=admin_header,
    ).json()
    visible_zip = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": visible["id"]},
        headers=admin_header,
    ).json()
    hidden_zip = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    ).json()
    hidden_project_zip = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": hidden_project["id"]},
        headers=admin_header,
    ).json()
    visible_csvutil = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": visible["id"]},
        headers=admin_header,
    ).json()
    hidden_csvutil_build = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    ).json()
    hidden_project_csvutil = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": hidden_project["id"]},
        headers=admin_header,
    ).json()
    visible_checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{visible['id']}",
        headers=admin_header,
    ).json()
    hidden_checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{hidden_domain['id']}",
        headers=admin_header,
    ).json()
    visible_sequence = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": visible["id"]},
        headers=admin_header,
    ).json()
    hidden_sequence = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    ).json()
    visible_readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": visible["id"]},
        headers=admin_header,
    ).json()["items"][0]
    hidden_readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    ).json()["items"][0]
    visible_readiness_export = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{visible_readiness['id']}/export",
        headers=admin_header,
    ).json()
    hidden_readiness_export = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{hidden_readiness['id']}/export",
        headers=admin_header,
    ).json()
    visible_handoff = LoadPlanCutoverHandoff(
        project_id=project_id,
        environment_id=environment_id,
        package_id=visible["id"],
        readiness_id=visible_readiness["id"],
        readiness_export_id=visible_readiness_export["id"],
        archive_evidence_id="visible_archive_evidence",
        summary_json=json.dumps({"package_id": visible["id"], "catalog_macro_object_code": "RATE_RECORD"}),
        committed_by="admin@example.com",
    )
    hidden_handoff = LoadPlanCutoverHandoff(
        project_id=project_id,
        environment_id=environment_id,
        package_id=hidden_domain["id"],
        readiness_id=hidden_readiness["id"],
        readiness_export_id=hidden_readiness_export["id"],
        archive_evidence_id="hidden_archive_evidence",
        summary_json=json.dumps({"package_id": hidden_domain["id"], "catalog_macro_object_code": "RATE_RECORD"}),
        committed_by="admin@example.com",
    )
    visible_review_item = LoadPlanReviewItem(
        project_id=project_id,
        environment_id=environment_id,
        package_id=visible["id"],
        zip_analysis_id=visible_zip["id"],
        source_code="SYNTHETIC_VISIBLE_SCOPE",
        severity="WARNING",
        category="STRUCTURE",
        title="Visible synthetic review item",
        description="Synthetic review item for active context.",
        details_json="{}",
        created_by="admin@example.com",
    )
    hidden_review_item = LoadPlanReviewItem(
        project_id=project_id,
        environment_id=environment_id,
        package_id=hidden_domain["id"],
        zip_analysis_id=hidden_zip["id"],
        source_code="SYNTHETIC_HIDDEN_SCOPE",
        severity="WARNING",
        category="STRUCTURE",
        title="Hidden synthetic review item",
        description="Synthetic review item outside active context.",
        details_json="{}",
        created_by="admin@example.com",
    )
    db_session.add_all([visible_handoff, hidden_handoff, visible_review_item, hidden_review_item])
    db_session.commit()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/load-plan/packages", headers=admin_header)
    visible_detail = client.get(f"/api/v1/modules/load-plan/packages/{visible['id']}", headers=admin_header)
    hidden_detail = client.get(
        f"/api/v1/modules/load-plan/packages/{hidden_domain['id']}",
        headers=admin_header,
    )
    hidden_project_detail = client.get(
        f"/api/v1/modules/load-plan/packages/{hidden_project['id']}",
        headers=admin_header,
    )
    hidden_register = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{hidden_domain_batch['id']}",
        headers=admin_header,
    )
    hidden_project_register = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{hidden_project_batch['id']}",
        headers=admin_header,
    )
    hidden_zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    )
    hidden_csvutil = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": hidden_domain["id"]},
        headers=admin_header,
    )
    hidden_checklist_create = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{hidden_domain['id']}",
        headers=admin_header,
    )
    zip_list = client.get("/api/v1/modules/load-plan/zip-analysis", headers=admin_header)
    visible_zip_detail = client.get(
        f"/api/v1/modules/load-plan/zip-analysis/{visible_zip['id']}",
        headers=admin_header,
    )
    hidden_zip_detail = client.get(
        f"/api/v1/modules/load-plan/zip-analysis/{hidden_zip['id']}",
        headers=admin_header,
    )
    hidden_project_zip_detail = client.get(
        f"/api/v1/modules/load-plan/zip-analysis/{hidden_project_zip['id']}",
        headers=admin_header,
    )
    csvutil_list = client.get("/api/v1/modules/load-plan/csvutil/builds", headers=admin_header)
    visible_csvutil_detail = client.get(
        f"/api/v1/modules/load-plan/csvutil/builds/{visible_csvutil['id']}",
        headers=admin_header,
    )
    hidden_csvutil_detail = client.get(
        f"/api/v1/modules/load-plan/csvutil/builds/{hidden_csvutil_build['id']}",
        headers=admin_header,
    )
    hidden_project_csvutil_detail = client.get(
        f"/api/v1/modules/load-plan/csvutil/builds/{hidden_project_csvutil['id']}",
        headers=admin_header,
    )
    visible_checklist_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-checklists/{visible_checklist['id']}",
        headers=admin_header,
    )
    hidden_checklist_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-checklists/{hidden_checklist['id']}",
        headers=admin_header,
    )
    hidden_checklist_readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{hidden_checklist['id']}/readiness",
        headers=admin_header,
    )
    hidden_checklist_export = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{hidden_checklist['id']}/export-package",
        headers=admin_header,
    )
    hidden_checklist_go_no_go = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{hidden_checklist['id']}/go-no-go",
        json={"decision_note": "Synthetic blocked scope check"},
        headers=admin_header,
    )
    hidden_csvutil_from_checklist = client.post(
        f"/api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{hidden_checklist['id']}",
        json={},
        headers=admin_header,
    )
    sequence_list = client.get("/api/v1/modules/load-plan/sequence/snapshots", headers=admin_header)
    visible_sequence_detail = client.get(
        f"/api/v1/modules/load-plan/sequence/snapshots/{visible_sequence['id']}",
        headers=admin_header,
    )
    visible_sequence_evidence = (
        db_session.query(Evidence)
        .filter(Evidence.id == visible_sequence["evidence_id"])
        .one()
    )
    hidden_sequence_detail = client.get(
        f"/api/v1/modules/load-plan/sequence/snapshots/{hidden_sequence['id']}",
        headers=admin_header,
    )
    hidden_latest_sequence = client.get(
        "/api/v1/modules/load-plan/sequence",
        params={"package_id": hidden_domain["id"]},
        headers=admin_header,
    )
    readiness_list = client.get("/api/v1/modules/load-plan/cutover-readiness", headers=admin_header)
    visible_readiness_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/{visible_readiness['id']}",
        headers=admin_header,
    )
    hidden_readiness_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/{hidden_readiness['id']}",
        headers=admin_header,
    )
    hidden_latest_readiness = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/latest",
        params={"package_id": hidden_domain["id"]},
        headers=admin_header,
    )
    hidden_readiness_export_create = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{hidden_readiness['id']}/export",
        headers=admin_header,
    )
    readiness_export_list = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports",
        headers=admin_header,
    )
    visible_readiness_export_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/exports/{visible_readiness_export['id']}",
        headers=admin_header,
    )
    hidden_readiness_export_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/exports/{hidden_readiness_export['id']}",
        headers=admin_header,
    )
    handoff_list = client.get("/api/v1/modules/load-plan/cutover-handoff", headers=admin_header)
    visible_handoff_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-handoff/{visible_handoff.id}",
        headers=admin_header,
    )
    hidden_handoff_detail = client.get(
        f"/api/v1/modules/load-plan/cutover-handoff/{hidden_handoff.id}",
        headers=admin_header,
    )
    hidden_review_generation = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{hidden_zip['id']}",
        headers=admin_header,
    )
    review_list = client.get("/api/v1/modules/load-plan/review-queue", headers=admin_header)
    visible_review_detail = client.get(
        f"/api/v1/modules/load-plan/review-queue/{visible_review_item.id}",
        headers=admin_header,
    )
    hidden_review_detail = client.get(
        f"/api/v1/modules/load-plan/review-queue/{hidden_review_item.id}",
        headers=admin_header,
    )
    hidden_review_decide = client.post(
        f"/api/v1/modules/load-plan/review-queue/{hidden_review_item.id}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic hidden decision"},
        headers=admin_header,
    )
    summary = client.get("/api/v1/modules/load-plan/summary", headers=admin_header)

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [visible["id"]]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["id"]
    assert hidden_detail.status_code == 404
    assert hidden_project_detail.status_code == 404
    assert hidden_register.status_code == 404
    assert hidden_project_register.status_code == 404
    assert hidden_zip_analysis.status_code == 404
    assert hidden_csvutil.status_code == 404
    assert hidden_checklist_create.status_code == 404
    assert zip_list.status_code == 200
    assert [item["id"] for item in zip_list.json()["items"]] == [visible_zip["id"]]
    assert visible_zip_detail.status_code == 200
    assert visible_zip_detail.json()["id"] == visible_zip["id"]
    assert hidden_zip_detail.status_code == 404
    assert hidden_project_zip_detail.status_code == 404
    assert csvutil_list.status_code == 200
    assert [item["id"] for item in csvutil_list.json()["items"]] == [visible_csvutil["id"]]
    assert visible_csvutil_detail.status_code == 200
    assert visible_csvutil_detail.json()["id"] == visible_csvutil["id"]
    assert hidden_csvutil_detail.status_code == 404
    assert hidden_project_csvutil_detail.status_code == 404
    assert visible_checklist_detail.status_code == 200
    assert visible_checklist_detail.json()["id"] == visible_checklist["id"]
    assert hidden_checklist_detail.status_code == 404
    assert hidden_checklist_readiness.status_code == 404
    assert hidden_checklist_export.status_code == 404
    assert hidden_checklist_go_no_go.status_code == 404
    assert hidden_csvutil_from_checklist.status_code == 404
    assert sequence_list.status_code == 200
    assert [item["id"] for item in sequence_list.json()["items"]] == [visible_sequence["id"]]
    assert visible_sequence_detail.status_code == 200
    assert visible_sequence_detail.json()["id"] == visible_sequence["id"]
    assert visible_sequence_evidence.project_id == project_id
    assert visible_sequence_evidence.environment_id == environment_id
    assert visible_sequence_evidence.domain_name == "OTM1"
    assert visible_sequence_evidence.visibility == "PROJECT"
    assert hidden_sequence_detail.status_code == 404
    assert hidden_latest_sequence.status_code == 404
    assert readiness_list.status_code == 200
    assert [item["id"] for item in readiness_list.json()["items"]] == [visible_readiness["id"]]
    assert visible_readiness_detail.status_code == 200
    assert visible_readiness_detail.json()["id"] == visible_readiness["id"]
    assert hidden_readiness_detail.status_code == 404
    assert hidden_latest_readiness.status_code == 404
    assert hidden_readiness_export_create.status_code == 404
    assert readiness_export_list.status_code == 200
    assert [item["id"] for item in readiness_export_list.json()["items"]] == [visible_readiness_export["id"]]
    assert visible_readiness_export_detail.status_code == 200
    assert visible_readiness_export_detail.json()["id"] == visible_readiness_export["id"]
    assert hidden_readiness_export_detail.status_code == 404
    assert handoff_list.status_code == 200
    assert [item["id"] for item in handoff_list.json()["items"]] == [visible_handoff.id]
    assert visible_handoff_detail.status_code == 200
    assert visible_handoff_detail.json()["id"] == visible_handoff.id
    assert hidden_handoff_detail.status_code == 404
    assert hidden_review_generation.status_code == 404
    assert review_list.status_code == 200
    assert [item["id"] for item in review_list.json()["items"]] == [visible_review_item.id]
    assert visible_review_detail.status_code == 200
    assert visible_review_detail.json()["id"] == visible_review_item.id
    assert hidden_review_detail.status_code == 404
    assert hidden_review_decide.status_code == 404
    assert summary.status_code == 200
    assert summary.json()["registered_packages"] == 1


def test_load_plan_packages_require_active_context_for_non_admin_access_and_register(
    client,
    admin_header,
    auth_header,
):
    visible_batch, _, _ = prepare_approved_exported_rate_batch(client, admin_header)
    source_batch, _, _ = prepare_approved_exported_rate_batch(client, admin_header, domain_name="OTM2")
    master_data_batch, _ = prepare_exported_master_data_locations_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{visible_batch['id']}",
        headers=admin_header,
    ).json()
    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{created['id']}",
        headers=admin_header,
    ).json()
    checklist_item = next(item for item in checklist["items"] if item["item_code"] == "TABLE_READY")

    listed = client.get("/api/v1/modules/load-plan/packages", headers=auth_header)
    summary = client.get("/api/v1/modules/load-plan/summary", headers=auth_header)
    detail = client.get(f"/api/v1/modules/load-plan/packages/{created['id']}", headers=auth_header)
    register = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{source_batch['id']}",
        headers=auth_header,
    )
    register_master_data = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{master_data_batch['batch_id']}",
        headers=auth_header,
    )
    zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": created["id"]},
        headers=auth_header,
    )
    csvutil = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": created["id"]},
        headers=auth_header,
    )
    checklist_create = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{created['id']}",
        headers=auth_header,
    )
    checklist_update = client.patch(
        f"/api/v1/modules/load-plan/cutover-checklists/items/{checklist_item['id']}",
        json={"status": "DONE", "method": "MANUAL"},
        headers=auth_header,
    )
    sequence_snapshot = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": created["id"]},
        headers=auth_header,
    )
    cutover_readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": created["id"]},
        headers=auth_header,
    )
    handoff_eligibility = client.get(
        "/api/v1/modules/load-plan/cutover-handoff/eligibility",
        params={"package_id": created["id"]},
        headers=auth_header,
    )
    handoff_create = client.post(
        "/api/v1/modules/load-plan/cutover-handoff",
        json={"package_id": created["id"]},
        headers=auth_header,
    )

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0
    assert summary.status_code == 200
    assert summary.json()["registered_packages"] == 0
    assert detail.status_code == 404
    assert register.status_code == 404
    assert register_master_data.status_code == 404
    assert zip_analysis.status_code == 404
    assert csvutil.status_code == 404
    assert checklist_create.status_code == 404
    assert checklist_update.status_code == 404
    assert sequence_snapshot.status_code == 404
    assert cutover_readiness.status_code == 404
    assert handoff_eligibility.status_code == 404
    assert handoff_create.status_code == 404


def test_load_plan_package_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, environment_id = create_project_environment(client, admin_header)
    otm1_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    otm2_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    other_environment_batch, _, _ = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id="env_dev",
        domain_name="OTM3",
    )
    otm1 = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{otm1_batch['id']}",
        headers=admin_header,
    ).json()
    otm2 = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{otm2_batch['id']}",
        headers=admin_header,
    ).json()
    client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{other_environment_batch['id']}",
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
        can_view_all_domains=True,
    )

    listed = client.get("/api/v1/modules/load-plan/packages", headers=admin_header)

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}


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
    project_id, environment_id = create_project_environment(client, admin_header)
    batch, export, approval = prepare_approved_exported_rate_batch(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )

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
    assert evidence.project_id == project_id
    assert evidence.environment_id == environment_id
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
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
    project_id, environment_id = create_project_environment(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
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
    assert package.project_id == project_id
    assert package.environment_id == environment_id
    assert package.domain_name == "OTM1"
    assert package.created_by == "admin@example.com"
    assert package.registered_at is not None


def test_operational_master_data_package_reaches_zip_analysis_and_cutover_readiness(
    client,
    admin_header,
):
    batch, export = prepare_exported_operational_locations_batch(client, admin_header)
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    ).json()

    assert package["artifact_id"] == export["artifact_id"]
    assert package["summary"]["catalog_macro_object_code"] == "LOCATION"
    assert [item["table_name"] for item in package["load_sequence"]] == [
        "EQUIPMENT_GROUP_PROFILE",
        "EQUIPMENT_GROUP_PROFILE_D",
        "LOCATION",
        "LOCATION_ADDRESS",
        "LOCATION_CAPACITY",
        "LOCATION_ACTIVITY_TIME_DEF",
        "LOCATION_LOAD_UNLOAD_POINT",
    ]

    zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert zip_analysis.status_code == 200
    zip_payload = zip_analysis.json()
    assert zip_payload["summary"]["error_count"] == 0, zip_payload["findings"]
    assert zip_payload["summary"]["csv_file_count"] == 7

    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    ).json()

    assert readiness["summary"]["latest_zip_analysis_id"] == zip_payload["id"]
    master_data_family = next(
        family for family in readiness["summary"]["package_families"] if family["family_code"] == "MASTER_DATA"
    )
    assert master_data_family["table_count"] == 7
    assert readiness["status"] == "BLOCKED"
    assert not any(blocker["code"] == "ZIP_ANALYSIS_ERROR" for blocker in readiness["blockers"])
    assert "SYN.LOC_DC_001" not in json.dumps(zip_payload)
    assert "SYN.LOC_DC_001" not in json.dumps(readiness)


def test_operational_location_master_data_blocks_orphan_dock_before_batch_creation(
    client,
    admin_header,
):
    response = create_operational_locations_batch_with_missing_location_parent(client, admin_header)

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "MASTER_DATA_WORKBOOK_EDITOR_INVALID"
    orphan = next(
        issue
        for issue in payload["details"]["validation"]["issues"]
        if issue["field_key"] == "dock_location_gid"
    )
    assert orphan["code"] == "RELATIONSHIP_PARENT_NOT_FOUND"
    assert orphan["sheet_code"] == "LOCATION_DOCKS"
    assert orphan["parent_sheet_code"] == "LOCATIONS"
    assert orphan["message"].endswith("LOCATIONS.location_gid.")


def test_item_packaging_master_data_package_reaches_zip_analysis_and_cutover_readiness(
    client,
    admin_header,
):
    batch, export = prepare_exported_item_packaging_batch(client, admin_header)
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-master-data/{batch['batch_id']}",
        headers=admin_header,
    ).json()

    assert package["artifact_id"] == export["artifact_id"]
    assert package["summary"]["catalog_macro_object_code"] == "ITEM"
    assert [item["table_name"] for item in package["load_sequence"]] == [
        "ITEM",
        "SHIP_UNIT_SPEC",
        "PACKAGED_ITEM",
        "TI_HI",
    ]

    zip_analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert zip_analysis.status_code == 200
    zip_payload = zip_analysis.json()
    assert zip_payload["summary"]["error_count"] == 0, zip_payload["findings"]
    assert zip_payload["summary"]["csv_file_count"] == 4

    checklist = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/from-package/{package['id']}",
        headers=admin_header,
    ).json()
    readiness = client.post(
        f"/api/v1/modules/load-plan/cutover-checklists/{checklist['id']}/readiness",
        headers=admin_header,
    ).json()

    assert readiness["summary"]["latest_zip_analysis_id"] == zip_payload["id"]
    master_data_family = next(
        family for family in readiness["summary"]["package_families"] if family["family_code"] == "MASTER_DATA"
    )
    assert master_data_family["table_count"] == 4
    assert readiness["status"] == "BLOCKED"
    assert not any(blocker["code"] == "ZIP_ANALYSIS_ERROR" for blocker in readiness["blockers"])
    assert "SYN.ITEM_WIDGET_001" not in json.dumps(zip_payload)
    assert "SYN.ITEM_WIDGET_001" not in json.dumps(readiness)


def test_item_packaging_master_data_blocks_orphan_transport_handling_unit_before_mapping(
    client,
    admin_header,
):
    response = create_item_packaging_batch_with_missing_transport_unit_parent(client, admin_header)

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "MASTER_DATA_WORKBOOK_EDITOR_INVALID"
    assert "validation" in payload["details"], payload
    orphan = next(
        issue
        for issue in payload["details"]["validation"]["issues"]
        if issue["field_key"] == "transport_handling_unit_gid"
    )
    assert orphan["code"] == "RELATIONSHIP_PARENT_NOT_FOUND"
    assert orphan["parent_sheet_code"] == "SHIP_UNIT_SPECS"
    assert orphan["message"].endswith("SHIP_UNIT_SPECS.ship_unit_spec_gid.")


def test_register_master_data_package_creates_client_safe_evidence_audit_and_event(
    client,
    admin_header,
    db_session,
):
    project_id, environment_id = create_project_environment(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
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
    assert evidence.project_id == project_id
    assert evidence.environment_id == environment_id
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    assert "OTM1.LOC_SYN_001" not in evidence.summary_json
    assert audit_metadata["catalog_macro_object_code"] == "LOCATION"
    assert event_payload["catalog_macro_object_code"] == "LOCATION"
    assert event_payload["package_type"] == "master_data_csv_zip"
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.project_id == project_id
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
