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


def test_rates_validate_load_sequence_api_reports_dependencies(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/dictionary/validate-load-sequence",
        json={"tables": ["RATE_GEO_COST"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert any(item["parent_table_name"] == "RATE_GEO_COST_GROUP" for item in response.json()["issues"])
