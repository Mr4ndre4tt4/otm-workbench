from otm_workbench.modules.rates.scenarios import get_rate_scenario, list_rate_scenarios


def test_rate_scenarios_include_initial_three_contracts():
    scenarios = list_rate_scenarios()

    assert [item.code for item in scenarios] == [
        "COMPLETE_TARIFF",
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


def test_rates_templates_api_returns_scenarios(client, admin_header):
    response = client.get("/api/v1/modules/rates/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["items"][0]["code"] == "COMPLETE_TARIFF"
