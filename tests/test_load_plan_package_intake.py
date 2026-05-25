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


def prepare_exported_operational_locations_batch(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "LOCATION_OPERATIONAL")
    editor_payload = {
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


def prepare_exported_item_packaging_batch(client, admin_header):
    template_code = create_master_data_template_from_scenario_pack(client, admin_header, "ITEM_PACKAGING_OPERATIONAL")
    editor_payload = {
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
