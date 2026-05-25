"""Backend-owned Master Data scenario packs.

Scenario packs are reusable starting points for realistic OTM template authoring.
They intentionally stay synthetic and Data Dictionary-backed.
"""

from copy import deepcopy


def _field(
    field_key: str,
    label: str,
    sheet_code: str,
    *,
    data_type: str = "string",
    required: bool = False,
) -> dict[str, object]:
    return {
        "field_key": field_key,
        "label": label,
        "data_type": data_type,
        "required": required,
        "sheet_code": sheet_code,
    }


def _user_mapping(
    mapping_key: str,
    source_field_key: str,
    target_table: str,
    target_column: str,
    *,
    required: bool = False,
) -> dict[str, object]:
    return {
        "mapping_key": mapping_key,
        "source_type": "USER_FIELD",
        "source_field_key": source_field_key,
        "target_table": target_table,
        "target_column": target_column,
        "required": required,
    }


def _relationship(
    rule_key: str,
    parent_sheet_code: str,
    parent_field_key: str,
    child_sheet_code: str,
    child_field_key: str,
) -> dict[str, object]:
    return {
        "rule_key": rule_key,
        "parent_sheet_code": parent_sheet_code,
        "parent_field_key": parent_field_key,
        "child_sheet_code": child_sheet_code,
        "child_field_key": child_field_key,
        "severity": "ERROR",
    }


LOCATION_OPERATIONAL_DRAFT = {
    "code": "LOCATIONS_OPERATIONAL_QA",
    "name": "Locations Operational QA",
    "catalog_macro_object_code": "LOCATION",
    "data_category": "MASTER_DATA",
    "target_tables": [
        {"table_name": "EQUIPMENT_GROUP_PROFILE", "sequence": 10, "required": False},
        {"table_name": "EQUIPMENT_GROUP_PROFILE_D", "sequence": 20, "required": False},
        {"table_name": "LOCATION", "sequence": 30, "required": True},
        {"table_name": "LOCATION_ADDRESS", "sequence": 40, "required": False},
        {"table_name": "LOCATION_CAPACITY", "sequence": 50, "required": False},
        {"table_name": "LOCATION_ACTIVITY_TIME_DEF", "sequence": 60, "required": False},
        {"table_name": "LOCATION_LOAD_UNLOAD_POINT", "sequence": 70, "required": False},
    ],
    "sheets": [
        {
            "code": "LOCATIONS",
            "name": "Locations",
            "sequence": 10,
            "field_keys": [
                "location_gid",
                "location_xid",
                "location_name",
                "city",
                "province_code",
                "postal_code",
                "country_code3_gid",
                "time_zone_gid",
                "lat",
                "lon",
                "location_equipment_group_profile_gid",
                "appointment_activity_type",
            ],
        },
        {
            "code": "LOCATION_ADDRESSES",
            "name": "Location Addresses",
            "sequence": 20,
            "field_keys": ["address_location_gid", "address_line_sequence", "address_line"],
        },
        {
            "code": "LOCATION_CAPACITIES",
            "name": "Location Capacities",
            "sequence": 30,
            "field_keys": [
                "capacity_location_gid",
                "location_capacity_gid",
                "location_capacity_xid",
                "capacity_calendar_gid",
            ],
        },
        {
            "code": "LOCATION_ACTIVITY_TIMES",
            "name": "Location Activity Times",
            "sequence": 40,
            "field_keys": ["activity_location_gid", "location_role_gid", "activity_time_def_gid"],
        },
        {
            "code": "LOCATION_DOCKS",
            "name": "Location Docks",
            "sequence": 50,
            "field_keys": [
                "dock_location_gid",
                "load_unload_point",
                "dock_equipment_group_profile_gid",
                "is_load",
                "load_sequence",
                "is_unload",
                "unload_sequence",
            ],
        },
        {
            "code": "EQUIPMENT_PROFILES",
            "name": "Equipment Profiles",
            "sequence": 60,
            "field_keys": [
                "equipment_group_profile_gid",
                "equipment_group_profile_xid",
                "equipment_group_profile_name",
            ],
        },
        {
            "code": "EQUIPMENT_PROFILE_DETAILS",
            "name": "Equipment Profile Details",
            "sequence": 70,
            "field_keys": ["detail_equipment_group_profile_gid", "equipment_group_gid"],
        },
    ],
    "fields": [
        _field("location_gid", "Location GID", "LOCATIONS", required=True),
        _field("location_xid", "Location XID", "LOCATIONS", required=True),
        _field("location_name", "Location Name", "LOCATIONS", required=True),
        _field("city", "City", "LOCATIONS"),
        _field("province_code", "Province Code", "LOCATIONS"),
        _field("postal_code", "Postal Code", "LOCATIONS"),
        _field("country_code3_gid", "Country Code", "LOCATIONS"),
        _field("time_zone_gid", "Time Zone", "LOCATIONS"),
        _field("lat", "Latitude", "LOCATIONS", data_type="number"),
        _field("lon", "Longitude", "LOCATIONS", data_type="number"),
        _field("location_equipment_group_profile_gid", "Equipment Restriction Profile", "LOCATIONS"),
        _field("appointment_activity_type", "Appointment Activity Type", "LOCATIONS"),
        _field("address_location_gid", "Address Location GID", "LOCATION_ADDRESSES", required=True),
        _field("address_line_sequence", "Address Line Sequence", "LOCATION_ADDRESSES", data_type="number", required=True),
        _field("address_line", "Address Line", "LOCATION_ADDRESSES"),
        _field("capacity_location_gid", "Capacity Location GID", "LOCATION_CAPACITIES", required=True),
        _field("location_capacity_gid", "Location Capacity GID", "LOCATION_CAPACITIES", required=True),
        _field("location_capacity_xid", "Location Capacity XID", "LOCATION_CAPACITIES", required=True),
        _field("capacity_calendar_gid", "Capacity Calendar GID", "LOCATION_CAPACITIES"),
        _field("activity_location_gid", "Activity Location GID", "LOCATION_ACTIVITY_TIMES", required=True),
        _field("location_role_gid", "Location Role GID", "LOCATION_ACTIVITY_TIMES", required=True),
        _field("activity_time_def_gid", "Activity Time Definition GID", "LOCATION_ACTIVITY_TIMES", required=True),
        _field("dock_location_gid", "Dock Location GID", "LOCATION_DOCKS", required=True),
        _field("load_unload_point", "Dock Code", "LOCATION_DOCKS", required=True),
        _field("dock_equipment_group_profile_gid", "Dock Equipment Profile", "LOCATION_DOCKS"),
        _field("is_load", "Is Load Dock", "LOCATION_DOCKS"),
        _field("load_sequence", "Load Sequence", "LOCATION_DOCKS", data_type="number"),
        _field("is_unload", "Is Unload Dock", "LOCATION_DOCKS"),
        _field("unload_sequence", "Unload Sequence", "LOCATION_DOCKS", data_type="number"),
        _field("equipment_group_profile_gid", "Equipment Profile GID", "EQUIPMENT_PROFILES", required=True),
        _field("equipment_group_profile_xid", "Equipment Profile XID", "EQUIPMENT_PROFILES", required=True),
        _field("equipment_group_profile_name", "Equipment Profile Name", "EQUIPMENT_PROFILES"),
        _field("detail_equipment_group_profile_gid", "Detail Equipment Profile GID", "EQUIPMENT_PROFILE_DETAILS", required=True),
        _field("equipment_group_gid", "Equipment Group GID", "EQUIPMENT_PROFILE_DETAILS", required=True),
    ],
    "mappings": [
        _user_mapping("location_gid", "location_gid", "LOCATION", "LOCATION_GID", required=True),
        _user_mapping("location_xid", "location_xid", "LOCATION", "LOCATION_XID", required=True),
        _user_mapping("location_name", "location_name", "LOCATION", "LOCATION_NAME", required=True),
        _user_mapping("location_city", "city", "LOCATION", "CITY"),
        _user_mapping("location_province", "province_code", "LOCATION", "PROVINCE_CODE"),
        _user_mapping("location_postal", "postal_code", "LOCATION", "POSTAL_CODE"),
        _user_mapping("location_country", "country_code3_gid", "LOCATION", "COUNTRY_CODE3_GID"),
        _user_mapping("location_timezone", "time_zone_gid", "LOCATION", "TIME_ZONE_GID"),
        _user_mapping("location_lat", "lat", "LOCATION", "LAT"),
        _user_mapping("location_lon", "lon", "LOCATION", "LON"),
        _user_mapping("location_equipment_profile", "location_equipment_group_profile_gid", "LOCATION", "SHUTTLE_LOT_EQ_GRP_PROFILE_GID"),
        _user_mapping("location_activity_type", "appointment_activity_type", "LOCATION", "APPOINTMENT_ACTIVITY_TYPE"),
        _user_mapping("address_location", "address_location_gid", "LOCATION_ADDRESS", "LOCATION_GID", required=True),
        _user_mapping("address_sequence", "address_line_sequence", "LOCATION_ADDRESS", "LINE_SEQUENCE", required=True),
        _user_mapping("address_line", "address_line", "LOCATION_ADDRESS", "ADDRESS_LINE"),
        _user_mapping("capacity_gid", "location_capacity_gid", "LOCATION_CAPACITY", "LOCATION_CAPACITY_GID", required=True),
        _user_mapping("capacity_xid", "location_capacity_xid", "LOCATION_CAPACITY", "LOCATION_CAPACITY_XID", required=True),
        _user_mapping("capacity_calendar", "capacity_calendar_gid", "LOCATION_CAPACITY", "CALENDAR_GID"),
        _user_mapping("activity_location", "activity_location_gid", "LOCATION_ACTIVITY_TIME_DEF", "LOCATION_GID", required=True),
        _user_mapping("activity_role", "location_role_gid", "LOCATION_ACTIVITY_TIME_DEF", "LOCATION_ROLE_GID", required=True),
        _user_mapping("activity_time_def", "activity_time_def_gid", "LOCATION_ACTIVITY_TIME_DEF", "ACTIVITY_TIME_DEF_GID", required=True),
        _user_mapping("dock_location", "dock_location_gid", "LOCATION_LOAD_UNLOAD_POINT", "LOCATION_GID", required=True),
        _user_mapping("dock_point", "load_unload_point", "LOCATION_LOAD_UNLOAD_POINT", "LOAD_UNLOAD_POINT", required=True),
        _user_mapping("dock_profile", "dock_equipment_group_profile_gid", "LOCATION_LOAD_UNLOAD_POINT", "EQUIPMENT_GROUP_PROFILE_GID"),
        _user_mapping("dock_is_load", "is_load", "LOCATION_LOAD_UNLOAD_POINT", "IS_LOAD"),
        _user_mapping("dock_load_sequence", "load_sequence", "LOCATION_LOAD_UNLOAD_POINT", "LOAD_SEQUENCE"),
        _user_mapping("dock_is_unload", "is_unload", "LOCATION_LOAD_UNLOAD_POINT", "IS_UNLOAD"),
        _user_mapping("dock_unload_sequence", "unload_sequence", "LOCATION_LOAD_UNLOAD_POINT", "UNLOAD_SEQUENCE"),
        _user_mapping("profile_gid", "equipment_group_profile_gid", "EQUIPMENT_GROUP_PROFILE", "EQUIPMENT_GROUP_PROFILE_GID", required=True),
        _user_mapping("profile_xid", "equipment_group_profile_xid", "EQUIPMENT_GROUP_PROFILE", "EQUIPMENT_GROUP_PROFILE_XID", required=True),
        _user_mapping("profile_name", "equipment_group_profile_name", "EQUIPMENT_GROUP_PROFILE", "EQUIPMENT_GROUP_PROFILE_NAME"),
        _user_mapping("profile_detail_gid", "detail_equipment_group_profile_gid", "EQUIPMENT_GROUP_PROFILE_D", "EQUIPMENT_GROUP_PROFILE_GID", required=True),
        _user_mapping("profile_detail_equipment_group", "equipment_group_gid", "EQUIPMENT_GROUP_PROFILE_D", "EQUIPMENT_GROUP_GID", required=True),
    ],
    "relationship_rules": [
        _relationship("location_address_parent", "LOCATIONS", "location_gid", "LOCATION_ADDRESSES", "address_location_gid"),
        _relationship("location_capacity_parent", "LOCATIONS", "location_gid", "LOCATION_CAPACITIES", "capacity_location_gid"),
        _relationship("location_activity_parent", "LOCATIONS", "location_gid", "LOCATION_ACTIVITY_TIMES", "activity_location_gid"),
        _relationship("location_dock_parent", "LOCATIONS", "location_gid", "LOCATION_DOCKS", "dock_location_gid"),
        _relationship("location_profile_parent", "EQUIPMENT_PROFILES", "equipment_group_profile_gid", "LOCATIONS", "location_equipment_group_profile_gid"),
        _relationship("profile_detail_parent", "EQUIPMENT_PROFILES", "equipment_group_profile_gid", "EQUIPMENT_PROFILE_DETAILS", "detail_equipment_group_profile_gid"),
    ],
    "documentation_refs": [
        {
            "source_type": "DATA_DICTIONARY",
            "scope": "LOCATION, LOCATION_ADDRESS, LOCATION_CAPACITY, LOCATION_ACTIVITY_TIME_DEF, LOCATION_LOAD_UNLOAD_POINT, EQUIPMENT_GROUP_PROFILE, EQUIPMENT_GROUP_PROFILE_D",
            "note": "Validated against local OTM Data Dictionary 26B.",
        },
        {
            "source_type": "ORACLE_OFFICIAL",
            "scope": "Equipment Group Profile, Activity Type Capacity, Activity Time Definition",
            "note": "Oracle Help confirms equipment profile restrictions, location capacity, and activity time concepts.",
        },
    ],
}

ITEM_PACKAGING_OPERATIONAL_DRAFT = {
    "code": "ITEM_PACKAGING_OPERATIONAL_QA",
    "name": "Item Packaging Operational QA",
    "catalog_macro_object_code": "ITEM",
    "data_category": "MASTER_DATA",
    "target_tables": [
        {"table_name": "ITEM", "sequence": 10, "required": True},
        {"table_name": "SHIP_UNIT_SPEC", "sequence": 20, "required": True},
        {"table_name": "PACKAGED_ITEM", "sequence": 30, "required": True},
        {"table_name": "TI_HI", "sequence": 40, "required": False},
    ],
    "sheets": [
        {"code": "ITEMS", "name": "Items", "sequence": 10, "field_keys": ["item_gid", "item_xid", "item_name", "item_type_gid", "unit_of_measure"]},
        {"code": "SHIP_UNIT_SPECS", "name": "Ship Unit Specs", "sequence": 20, "field_keys": ["ship_unit_spec_gid", "ship_unit_spec_xid", "ship_unit_spec_name", "unit_type", "length", "length_uom_code", "width", "width_uom_code", "height", "height_uom_code", "tare_weight", "tare_weight_uom_code", "effective_volume", "effective_volume_uom_code", "is_in_on_max"]},
        {"code": "PACKAGED_ITEMS", "name": "Packaged Items", "sequence": 30, "field_keys": ["packaged_item_gid", "packaged_item_xid", "package_item_gid", "packaging_unit_gid", "package_ship_unit_weight", "package_ship_unit_weight_uom", "package_su_volume", "package_su_volume_uom_code", "package_su_length", "package_su_length_uom_code", "package_su_width", "package_su_width_uom_code", "package_su_height", "package_su_height_uom_code"]},
        {"code": "TI_HI", "name": "TiHi", "sequence": 40, "field_keys": ["tihi_sequence_no", "tihi_packaged_item_gid", "tihi_packaging_unit_gid", "transport_handling_unit_gid", "num_layers", "quantity_per_layer"]},
    ],
    "fields": [
        _field("item_gid", "Item GID", "ITEMS", required=True),
        _field("item_xid", "Item XID", "ITEMS", required=True),
        _field("item_name", "Item Name", "ITEMS"),
        _field("item_type_gid", "Item Type GID", "ITEMS"),
        _field("unit_of_measure", "Unit of Measure", "ITEMS"),
        *[_field(key, label, "SHIP_UNIT_SPECS", data_type=data_type, required=required) for key, label, data_type, required in [
            ("ship_unit_spec_gid", "Ship Unit Spec GID", "string", True),
            ("ship_unit_spec_xid", "Ship Unit Spec XID", "string", True),
            ("ship_unit_spec_name", "Ship Unit Spec Name", "string", False),
            ("unit_type", "Unit Type", "string", True),
            ("length", "Length", "number", False),
            ("length_uom_code", "Length UOM", "string", False),
            ("width", "Width", "number", False),
            ("width_uom_code", "Width UOM", "string", False),
            ("height", "Height", "number", False),
            ("height_uom_code", "Height UOM", "string", False),
            ("tare_weight", "Tare Weight", "number", False),
            ("tare_weight_uom_code", "Tare Weight UOM", "string", False),
            ("effective_volume", "Effective Volume", "number", False),
            ("effective_volume_uom_code", "Effective Volume UOM", "string", False),
            ("is_in_on_max", "Inside/On Max", "string", False),
        ]],
        *[_field(key, label, "PACKAGED_ITEMS", data_type=data_type, required=required) for key, label, data_type, required in [
            ("packaged_item_gid", "Packaged Item GID", "string", True),
            ("packaged_item_xid", "Packaged Item XID", "string", True),
            ("package_item_gid", "Item GID", "string", True),
            ("packaging_unit_gid", "Packaging Unit GID", "string", True),
            ("package_ship_unit_weight", "Package Weight", "number", False),
            ("package_ship_unit_weight_uom", "Package Weight UOM", "string", False),
            ("package_su_volume", "Package Volume", "number", False),
            ("package_su_volume_uom_code", "Package Volume UOM", "string", False),
            ("package_su_length", "Package Length", "number", False),
            ("package_su_length_uom_code", "Package Length UOM", "string", False),
            ("package_su_width", "Package Width", "number", False),
            ("package_su_width_uom_code", "Package Width UOM", "string", False),
            ("package_su_height", "Package Height", "number", False),
            ("package_su_height_uom_code", "Package Height UOM", "string", False),
        ]],
        _field("tihi_sequence_no", "TiHi Sequence", "TI_HI", data_type="number", required=True),
        _field("tihi_packaged_item_gid", "Packaged Item GID", "TI_HI", required=True),
        _field("tihi_packaging_unit_gid", "Packaging Unit GID", "TI_HI", required=True),
        _field("transport_handling_unit_gid", "Transport Handling Unit GID", "TI_HI", required=True),
        _field("num_layers", "Number of Layers", "TI_HI", data_type="number", required=True),
        _field("quantity_per_layer", "Quantity per Layer", "TI_HI", data_type="number", required=True),
    ],
    "mappings": [
        _user_mapping("item_gid", "item_gid", "ITEM", "ITEM_GID", required=True),
        _user_mapping("item_xid", "item_xid", "ITEM", "ITEM_XID", required=True),
        _user_mapping("item_name", "item_name", "ITEM", "ITEM_NAME"),
        _user_mapping("item_type", "item_type_gid", "ITEM", "ITEM_TYPE_GID"),
        _user_mapping("item_uom", "unit_of_measure", "ITEM", "UNIT_OF_MEASURE"),
        *[_user_mapping(f"sus_{column.lower()}", column.lower(), "SHIP_UNIT_SPEC", column, required=column in {"SHIP_UNIT_SPEC_GID", "SHIP_UNIT_SPEC_XID", "UNIT_TYPE"}) for column in [
            "SHIP_UNIT_SPEC_GID", "SHIP_UNIT_SPEC_XID", "SHIP_UNIT_SPEC_NAME", "UNIT_TYPE", "LENGTH", "LENGTH_UOM_CODE", "WIDTH", "WIDTH_UOM_CODE", "HEIGHT", "HEIGHT_UOM_CODE", "TARE_WEIGHT", "TARE_WEIGHT_UOM_CODE", "EFFECTIVE_VOLUME", "EFFECTIVE_VOLUME_UOM_CODE", "IS_IN_ON_MAX"
        ]],
        _user_mapping("packaged_item_gid", "packaged_item_gid", "PACKAGED_ITEM", "PACKAGED_ITEM_GID", required=True),
        _user_mapping("packaged_item_xid", "packaged_item_xid", "PACKAGED_ITEM", "PACKAGED_ITEM_XID", required=True),
        _user_mapping("packaged_item_item", "package_item_gid", "PACKAGED_ITEM", "ITEM_GID", required=True),
        _user_mapping("packaged_item_packaging_unit", "packaging_unit_gid", "PACKAGED_ITEM", "PACKAGING_UNIT_GID", required=True),
        *[_user_mapping(f"packaged_item_{column.lower()}", column.lower(), "PACKAGED_ITEM", column) for column in [
            "PACKAGE_SHIP_UNIT_WEIGHT", "PACKAGE_SHIP_UNIT_WEIGHT_UOM", "PACKAGE_SU_VOLUME", "PACKAGE_SU_VOLUME_UOM_CODE", "PACKAGE_SU_LENGTH", "PACKAGE_SU_LENGTH_UOM_CODE", "PACKAGE_SU_WIDTH", "PACKAGE_SU_WIDTH_UOM_CODE", "PACKAGE_SU_HEIGHT", "PACKAGE_SU_HEIGHT_UOM_CODE"
        ]],
        _user_mapping("tihi_sequence", "tihi_sequence_no", "TI_HI", "SEQUENCE_NO", required=True),
        _user_mapping("tihi_packaged_item", "tihi_packaged_item_gid", "TI_HI", "PACKAGED_ITEM_GID", required=True),
        _user_mapping("tihi_packaging_unit", "tihi_packaging_unit_gid", "TI_HI", "PACKAGING_UNIT_GID", required=True),
        _user_mapping("tihi_thu", "transport_handling_unit_gid", "TI_HI", "TRANSPORT_HANDLING_UNIT_GID", required=True),
        _user_mapping("tihi_layers", "num_layers", "TI_HI", "NUM_LAYERS", required=True),
        _user_mapping("tihi_qty_layer", "quantity_per_layer", "TI_HI", "QUANTITY_PER_LAYER", required=True),
    ],
    "relationship_rules": [
        _relationship("packaged_item_item_parent", "ITEMS", "item_gid", "PACKAGED_ITEMS", "package_item_gid"),
        _relationship("packaged_item_packaging_unit_parent", "SHIP_UNIT_SPECS", "ship_unit_spec_gid", "PACKAGED_ITEMS", "packaging_unit_gid"),
        _relationship("tihi_packaged_item_parent", "PACKAGED_ITEMS", "packaged_item_gid", "TI_HI", "tihi_packaged_item_gid"),
        _relationship("tihi_packaging_unit_parent", "SHIP_UNIT_SPECS", "ship_unit_spec_gid", "TI_HI", "tihi_packaging_unit_gid"),
        _relationship("tihi_thu_parent", "SHIP_UNIT_SPECS", "ship_unit_spec_gid", "TI_HI", "transport_handling_unit_gid"),
    ],
    "documentation_refs": [
        {
            "source_type": "DATA_DICTIONARY",
            "scope": "ITEM, SHIP_UNIT_SPEC, PACKAGED_ITEM, TI_HI",
            "note": "Validated against local OTM Data Dictionary 26B.",
        },
        {
            "source_type": "ORACLE_OFFICIAL",
            "scope": "Packaged Item, TiHi, Ship Unit Calculation Logic",
            "note": "Oracle Help confirms the Item > Packaged Item > Ship Unit / TiHi hierarchy.",
        },
    ],
}


SCENARIO_PACKS = [
    {
        "code": "LOCATION_OPERATIONAL",
        "name": "Operational Location",
        "description": "Location setup with address, capacity reference, activity time, dock configuration, and equipment restrictions.",
        "draft_payload": LOCATION_OPERATIONAL_DRAFT,
    },
    {
        "code": "ITEM_PACKAGING_OPERATIONAL",
        "name": "Item Packaging",
        "description": "Item setup with Ship Unit Spec, Packaged Item, and TiHi hierarchy.",
        "draft_payload": ITEM_PACKAGING_OPERATIONAL_DRAFT,
    },
]


def list_master_data_scenario_packs() -> list[dict[str, object]]:
    packs = []
    for pack in SCENARIO_PACKS:
        draft_payload = deepcopy(pack["draft_payload"])
        packs.append(
            {
                "code": pack["code"],
                "name": pack["name"],
                "description": pack["description"],
                "catalog_macro_object_code": draft_payload["catalog_macro_object_code"],
                "target_tables": [table["table_name"] for table in draft_payload["target_tables"]],
                "summary": {
                    "sheet_count": len(draft_payload["sheets"]),
                    "field_count": len(draft_payload["fields"]),
                    "mapping_count": len(draft_payload["mappings"]),
                    "relationship_rule_count": len(draft_payload["relationship_rules"]),
                },
                "documentation_refs": draft_payload["documentation_refs"],
                "draft_payload": draft_payload,
            }
        )
    return packs
