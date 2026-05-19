from pathlib import Path

from otm_workbench.catalog.canonical import RATES_LOAD_SEQUENCE as CATALOG_RATES_LOAD_SEQUENCE
from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)
from otm_workbench.modules.rates.batches import table_sequence_index


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_rates_sequence_uses_catalog_core_canonical_sequence():
    assert RATES_LOAD_SEQUENCE == CATALOG_RATES_LOAD_SEQUENCE
    assert table_sequence_index("RATE_OFFERING") < table_sequence_index("RATE_GEO_COST")


def test_load_rate_geo_cost_definition_from_data_dictionary():
    definition = load_table_definition(DATA_DICT, "RATE_GEO_COST")

    assert definition.table_name == "RATE_GEO_COST"
    assert definition.primary_key == ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"]
    assert "RATE_GEO_COST_GROUP_GID" in definition.required_columns
    assert definition.foreign_keys[0].parent_table_name == "RATE_GEO_COST_GROUP"


def test_rates_load_sequence_tables_exist_in_data_dictionary():
    result = validate_load_sequence(DATA_DICT, RATES_LOAD_SEQUENCE)

    assert result.valid is True
    assert result.missing_tables == []
    assert "RATE_GEO_COST" in result.known_tables


def test_sequence_reports_fk_dependencies_that_are_outside_sequence():
    result = validate_load_sequence(DATA_DICT, ["RATE_GEO_COST"])

    assert result.valid is False
    assert any(
        issue.table_name == "RATE_GEO_COST"
        and issue.parent_table_name == "RATE_GEO_COST_GROUP"
        for issue in result.issues
    )


def test_rates_dictionary_table_api_returns_pk_and_date_columns(client, admin_header):
    response = client.get("/api/v1/modules/rates/dictionary/tables/RATE_GEO_COST", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["table_name"] == "RATE_GEO_COST"
    assert response.json()["primary_key"] == ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"]
    assert "ATTRIBUTE_DATE1" in response.json()["date_columns"]
    assert response.json()["data_category"] == "RATES_SETUP"
    assert response.json()["allow_csvutil"] is True
    assert response.json()["allow_cutover"] is True
    assert response.json()["is_transactional"] is False


def test_rates_dictionary_tables_filter_by_catalog_macro_object(client, admin_header):
    listed = client.get("/api/v1/modules/rates/dictionary/tables", headers=admin_header)
    catalog_matched = client.get(
        "/api/v1/modules/rates/dictionary/tables",
        params={"catalog_macro_object_code": "RATE_RECORD"},
        headers=admin_header,
    )
    catalog_unmatched = client.get(
        "/api/v1/modules/rates/dictionary/tables",
        params={"catalog_macro_object_code": "LOCATION"},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert catalog_matched.status_code == 200
    assert catalog_unmatched.status_code == 200
    assert listed.json()["total"] == len(RATES_LOAD_SEQUENCE)
    assert catalog_matched.json()["total"] == len(RATES_LOAD_SEQUENCE)
    assert catalog_matched.json()["items"][0]["table_name"] == RATES_LOAD_SEQUENCE[0]
    assert catalog_unmatched.json()["total"] == 0
    assert catalog_unmatched.json()["items"] == []


def test_rates_validate_load_sequence_api_reports_dependencies(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/dictionary/validate-load-sequence",
        json={"catalog_macro_object_code": "RATE_RECORD", "tables": ["RATE_GEO_COST"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["catalog_macro_object_code"] == "RATE_RECORD"
    assert response.json()["valid"] is False
    assert any(item["parent_table_name"] == "RATE_GEO_COST_GROUP" for item in response.json()["issues"])


def test_rates_validate_load_sequence_rejects_non_rates_catalog_macro_object(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/dictionary/validate-load-sequence",
        json={"catalog_macro_object_code": "LOCATION", "tables": ["LOCATION"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog_macro_object_code"] == "LOCATION"
    assert payload["valid"] is False
    assert payload["known_tables"] == []
    assert payload["missing_tables"] == []
    assert payload["issues"] == [
        {
            "severity": "ERROR",
            "table_name": "LOCATION",
            "parent_table_name": None,
            "message": "Catalog macro-object is outside the Rates module sequence.",
        }
    ]
