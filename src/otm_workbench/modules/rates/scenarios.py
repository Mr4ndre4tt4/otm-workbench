from dataclasses import dataclass

from otm_workbench.modules.rates.dictionary import RATES_LOAD_SEQUENCE

RATE_RECORD_MACRO_OBJECT_CODE = "RATE_RECORD"


@dataclass(frozen=True)
class RateScenario:
    code: str
    name: str
    description: str
    catalog_macro_object_code: str
    tables: list[str]
    required_tables: list[str]
    optional_tables: list[str]
    pre_existing_tables: list[str]

    @property
    def catalog_load_plan_path(self) -> str:
        return f"/api/v1/catalog/macro-objects/{self.catalog_macro_object_code}/load-plan"


SCENARIOS = [
    RateScenario(
        code="COMPLETE_TARIFF",
        name="Complete tariff",
        description="Rate offering plus rate geo, accessorial, and cost tables.",
        catalog_macro_object_code=RATE_RECORD_MACRO_OBJECT_CODE,
        tables=RATES_LOAD_SEQUENCE,
        required_tables=["X_LANE", "RATE_GEO", "RATE_GEO_COST_GROUP", "RATE_GEO_COST"],
        optional_tables=[
            "RATE_OFFERING",
            "RATE_UNIT_BREAK_PROFILE",
            "RATE_UNIT_BREAK",
            "ACCESSORIAL_CODE",
            "ACCESSORIAL_COST",
            "ACCESSORIAL_COST_UNIT_BREAK",
            "RATE_OFFERING_ACCESSORIAL",
            "RATE_GEO_ACCESSORIAL",
            "RATE_GEO_STOPS",
        ],
        pre_existing_tables=[],
    ),
    RateScenario(
        code="RATE_GEO_ONLY",
        name="Rate geo only",
        description="Rate records and costs when the offering exists or is handled separately.",
        catalog_macro_object_code=RATE_RECORD_MACRO_OBJECT_CODE,
        tables=[
            "X_LANE",
            "RATE_GEO",
            "ACCESSORIAL_COST",
            "RATE_GEO_ACCESSORIAL",
            "RATE_GEO_COST_GROUP",
            "RATE_GEO_COST",
        ],
        required_tables=["X_LANE", "RATE_GEO", "RATE_GEO_COST_GROUP", "RATE_GEO_COST"],
        optional_tables=["ACCESSORIAL_COST", "RATE_GEO_ACCESSORIAL"],
        pre_existing_tables=["RATE_OFFERING"],
    ),
    RateScenario(
        code="ACCESSORIAL_ONLY",
        name="Accessorial only",
        description="Accessorial costs and relationships without a full rate geo package.",
        catalog_macro_object_code=RATE_RECORD_MACRO_OBJECT_CODE,
        tables=["ACCESSORIAL_COST", "RATE_OFFERING_ACCESSORIAL", "RATE_GEO_ACCESSORIAL"],
        required_tables=["ACCESSORIAL_COST"],
        optional_tables=["RATE_OFFERING_ACCESSORIAL", "RATE_GEO_ACCESSORIAL"],
        pre_existing_tables=["RATE_OFFERING", "RATE_GEO", "ACCESSORIAL_CODE"],
    ),
]


def list_rate_scenarios() -> list[RateScenario]:
    return SCENARIOS


def get_rate_scenario(code: str) -> RateScenario:
    normalized = code.upper()
    for scenario in SCENARIOS:
        if scenario.code == normalized:
            return scenario
    raise ValueError(f"Unsupported rates scenario: {code}")


def requirement_for_table(scenario: RateScenario, table_name: str) -> str:
    table = table_name.upper()
    if table in scenario.required_tables:
        return "REQUIRED"
    if table in scenario.optional_tables:
        return "OPTIONAL"
    if table in scenario.pre_existing_tables:
        return "PRE_EXISTING"
    return "UNSUPPORTED"
