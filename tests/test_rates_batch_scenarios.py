from otm_workbench.modules.rates.scenarios import get_rate_scenario, list_rate_scenarios
from otm_workbench.modules.rates.dictionary import validate_load_sequence
from pathlib import Path


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_rate_scenarios_include_supported_contracts():
    scenarios = list_rate_scenarios()

    assert [item.code for item in scenarios] == [
        "COMPLETE_TARIFF",
        "LTL_TL_RATE_STACK",
        "RATE_GEO_ONLY",
        "ACCESSORIAL_ONLY",
    ]


def test_rate_geo_only_required_tables_are_explicit():
    scenario = get_rate_scenario("RATE_GEO_ONLY")

    assert scenario.required_tables == [
        "X_LANE",
        "RATE_GEO",
        "RATE_GEO_COST_GROUP",
        "RATE_GEO_COST",
    ]
    assert "RATE_OFFERING" in scenario.pre_existing_tables


def test_ltl_tl_rate_stack_sequence_matches_data_dictionary_dependencies():
    scenario = get_rate_scenario("LTL_TL_RATE_STACK")

    assert scenario.tables == [
        "RATE_OFFERING",
        "RATE_UNIT_BREAK_PROFILE",
        "RATE_UNIT_BREAK",
        "X_LANE",
        "RATE_GEO",
        "ACCESSORIAL_CODE",
        "ACCESSORIAL_COST",
        "ACCESSORIAL_COST_UNIT_BREAK",
        "RATE_OFFERING_ACCESSORIAL",
        "RATE_GEO_ACCESSORIAL",
        "RATE_GEO_STOPS",
        "RATE_GEO_COST_GROUP",
        "RATE_GEO_COST",
    ]
    assert scenario.required_tables == [
        "RATE_OFFERING",
        "RATE_UNIT_BREAK_PROFILE",
        "RATE_UNIT_BREAK",
        "X_LANE",
        "RATE_GEO",
        "RATE_GEO_COST_GROUP",
        "RATE_GEO_COST",
    ]
    assert scenario.optional_tables == [
        "ACCESSORIAL_CODE",
        "ACCESSORIAL_COST",
        "ACCESSORIAL_COST_UNIT_BREAK",
        "RATE_OFFERING_ACCESSORIAL",
        "RATE_GEO_ACCESSORIAL",
        "RATE_GEO_STOPS",
    ]
    assert scenario.pre_existing_tables == []
    result = validate_load_sequence(DATA_DICT, scenario.tables)
    assert result.valid is True
    assert result.missing_tables == []
    assert {issue.severity for issue in result.issues} <= {"WARNING"}
    assert not any(issue.parent_table_name in scenario.tables for issue in result.issues)


def test_rates_templates_api_returns_scenarios(client, admin_header):
    response = client.get("/api/v1/modules/rates/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert payload["items"][0]["code"] == "COMPLETE_TARIFF"


def test_rates_templates_include_catalog_context(client, admin_header):
    response = client.get("/api/v1/modules/rates/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    complete_tariff = payload["items"][0]
    assert complete_tariff["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        complete_tariff["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )


def test_rates_templates_filter_by_catalog_macro_object(client, admin_header):
    listed = client.get("/api/v1/modules/rates/templates", headers=admin_header)
    catalog_matched = client.get(
        "/api/v1/modules/rates/templates",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/rates/templates",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert catalog_matched.status_code == 200
    assert catalog_unmatched.status_code == 200
    assert listed.json()["total"] == 4
    assert catalog_matched.json()["total"] == 4
    assert [item["code"] for item in catalog_matched.json()["items"]] == [
        "COMPLETE_TARIFF",
        "LTL_TL_RATE_STACK",
        "RATE_GEO_ONLY",
        "ACCESSORIAL_ONLY",
    ]
    assert catalog_unmatched.json()["total"] == 0
    assert catalog_unmatched.json()["items"] == []
    assert catalog_unmatched.json()["code"] == "UNSUPPORTED_RATES_CATALOG_MACRO_OBJECT"
    assert catalog_unmatched.json()["message"] == "Catalog macro-object is outside the Rates module sequence."
    assert catalog_unmatched.json()["details"] == {"catalog_macro_object_code": "LOCATION"}
    assert catalog_unmatched.json()["catalog_macro_object_code"] == "LOCATION"


def test_created_rate_batch_includes_catalog_context(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/batches",
        headers=admin_header,
        json={"scenario_code": "RATE_GEO_ONLY", "name": "Synthetic rate geo", "domain_name": "OTM1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"


def test_rates_batch_list_filters_by_catalog_macro_object(client, admin_header):
    created = client.post(
        "/api/v1/modules/rates/batches",
        headers=admin_header,
        json={"scenario_code": "RATE_GEO_ONLY", "name": "Synthetic rate geo", "domain_name": "OTM1"},
    ).json()

    listed = client.get("/api/v1/modules/rates/batches", headers=admin_header)
    catalog_matched = client.get(
        "/api/v1/modules/rates/batches",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/rates/batches",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert catalog_matched.status_code == 200
    assert catalog_unmatched.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert catalog_matched.json()["total"] == 1
    assert catalog_matched.json()["items"][0]["id"] == created["id"]
    assert catalog_unmatched.json()["total"] == 0
    assert catalog_unmatched.json()["items"] == []
    assert catalog_unmatched.json()["code"] == "UNSUPPORTED_RATES_CATALOG_MACRO_OBJECT"
    assert catalog_unmatched.json()["message"] == "Catalog macro-object is outside the Rates module sequence."
    assert catalog_unmatched.json()["details"] == {"catalog_macro_object_code": "LOCATION"}
    assert catalog_unmatched.json()["catalog_macro_object_code"] == "LOCATION"
