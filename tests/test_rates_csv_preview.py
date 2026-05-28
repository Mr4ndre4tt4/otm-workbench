from pathlib import Path

from otm_workbench.config import get_settings
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview


DATA_DICT = Path(get_settings().otm_data_dictionary_root)


def test_otm_csv_preview_uses_table_first_then_columns():
    output = build_otm_csv_preview(
        DATA_DICT,
        table_name="RATE_GEO_COST",
        columns=["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ", "CHARGE_AMOUNT"],
        rows=[
            {
                "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1",
                "RATE_GEO_COST_SEQ": 1,
                "CHARGE_AMOUNT": 10,
            }
        ],
    )

    lines = output.splitlines()
    assert lines[0] == "RATE_GEO_COST"
    assert lines[1] == "RATE_GEO_COST_GROUP_GID,RATE_GEO_COST_SEQ,CHARGE_AMOUNT"
    assert lines[2] == "OTM1.RGCG_1,1,10"


def test_otm_csv_preview_adds_alter_session_for_date_columns():
    output = build_otm_csv_preview(
        DATA_DICT,
        table_name="RATE_OFFERING",
        columns=["RATE_OFFERING_GID", "ATTRIBUTE_DATE1"],
        rows=[
            {
                "RATE_OFFERING_GID": "OTM1.RO_1",
                "ATTRIBUTE_DATE1": "2026-05-18 10:00:00",
            }
        ],
    )

    lines = output.splitlines()
    assert lines[0] == "RATE_OFFERING"
    assert lines[1] == "RATE_OFFERING_GID,ATTRIBUTE_DATE1"
    assert lines[2] == "exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'"
    assert lines[3] == "OTM1.RO_1,2026-05-18 10:00:00"


def test_otm_csv_preview_rejects_unknown_columns():
    try:
        build_otm_csv_preview(
            DATA_DICT,
            table_name="RATE_GEO_COST",
            columns=["RATE_GEO_COST_GROUP_GID", "NOT_A_COLUMN"],
            rows=[{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1", "NOT_A_COLUMN": "x"}],
        )
    except ValueError as exc:
        assert "NOT_A_COLUMN" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown column")


def test_csv_preview_api(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/csv/preview",
        json={
            "catalog_macro_object_code": "RATE_RECORD",
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"],
            "rows": [{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1", "RATE_GEO_COST_SEQ": 1}],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["catalog_macro_object_code"] == "RATE_RECORD"
    assert (
        response.json()["catalog_load_plan_path"]
        == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    )
    assert response.json()["content"].splitlines()[0] == "RATE_GEO_COST"


def test_csv_preview_api_rejects_non_rates_catalog_macro_object(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/csv/preview",
        json={
            "catalog_macro_object_code": "LOCATION",
            "table_name": "LOCATION",
            "columns": ["LOCATION_GID"],
            "rows": [{"LOCATION_GID": "OTM1.LOC_A"}],
        },
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "UNSUPPORTED_RATES_CATALOG_MACRO_OBJECT"
    assert response.json()["message"] == "Catalog macro-object is outside the Rates module sequence."
    assert response.json()["details"] == {"catalog_macro_object_code": "LOCATION"}
