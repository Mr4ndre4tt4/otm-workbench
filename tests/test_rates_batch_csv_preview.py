from pathlib import Path

from otm_workbench.modules.rates.csv_preview import normalize_rows_for_otm_csv


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_rate_geo_seq_is_removed_from_csv_columns_and_rows():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO",
        ["RATE_GEO_GID", "RATE_GEO_SEQ"],
        [{"RATE_GEO_GID": "OTM1.RG_001", "RATE_GEO_SEQ": 99}],
    )

    assert columns == ["RATE_GEO_GID"]
    assert rows == [{"RATE_GEO_GID": "OTM1.RG_001"}]


def test_rate_geo_cost_group_seq_defaults_to_one():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO_COST_GROUP",
        ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_GID"],
        [{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "RATE_GEO_GID": "OTM1.RG_001"}],
    )

    assert "RATE_GEO_COST_GROUP_SEQ" in columns
    assert rows[0]["RATE_GEO_COST_GROUP_SEQ"] == 1


def test_rate_geo_cost_seq_increments_and_charge_amount_base_is_blank():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO_COST",
        ["RATE_GEO_COST_GROUP_GID", "CHARGE_AMOUNT", "CHARGE_AMOUNT_BASE"],
        [
            {"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "CHARGE_AMOUNT": 10, "CHARGE_AMOUNT_BASE": 10},
            {"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "CHARGE_AMOUNT": 20, "CHARGE_AMOUNT_BASE": 20},
        ],
    )

    assert "RATE_GEO_COST_SEQ" in columns
    assert rows[0]["RATE_GEO_COST_SEQ"] == 1
    assert rows[1]["RATE_GEO_COST_SEQ"] == 2
    assert rows[0]["CHARGE_AMOUNT_BASE"] is None
    assert rows[1]["CHARGE_AMOUNT_BASE"] is None
