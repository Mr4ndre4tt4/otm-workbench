def create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def test_validation_errors_when_required_table_missing(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={"tables": [{"table_name": "X_LANE", "rows": [{"X_LANE_GID": "OTM1.RG_001"}]}]},
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "REQUIRED_TABLE_MISSING" for issue in payload["issues"])


def test_validation_rejects_unknown_column(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY")
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [{"ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001", "NOT_A_COLUMN": "x"}],
                }
            ]
        },
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "UNKNOWN_COLUMN" for issue in payload["issues"])


def test_validation_applies_reference_policy_to_row_values(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="COMPLETE_TARIFF")
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "RATE_OFFERING",
                    "rows": [
                        {
                            "RATE_OFFERING_GID": "OTM1.RO_SYNTHETIC",
                            "RATE_OFFERING_XID": "RO_SYNTHETIC",
                            "RATE_OFFERING_TYPE_GID": "PUBLIC.CONTRACT",
                            "CURRENCY_GID": "OTM2.BRL",
                            "TRANSPORT_MODE_GID": "PUBLIC.TL",
                            "RATE_VERSION_GID": "OTM1.RV_001",
                            "EXCHANGE_RATE_GID": "PUBLIC.DEFAULT",
                            "COMMODITY_USAGE": "F",
                            "FAK_RATE_AS": "N",
                            "IS_DIGITAL_FREIGHT": "N",
                            "IS_MARKET_RATE": "N",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(
        issue["issue_code"] == "REFERENCE_POLICY_VIOLATION"
        and issue["column_name"] == "CURRENCY_GID"
        and "OTM2.BRL" in issue["details_json"]
        for issue in payload["issues"]
    )


def test_ltl_tl_rate_stack_batch_validates_internal_sequence(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="LTL_TL_RATE_STACK")
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "RATE_OFFERING",
                    "rows": [{"RATE_OFFERING_GID": "OTM1.RO_LTL_TL_001", "RATE_OFFERING_XID": "RO_LTL_TL_001"}],
                },
                {
                    "table_name": "RATE_UNIT_BREAK_PROFILE",
                    "rows": [
                        {
                            "RATE_UNIT_BREAK_PROFILE_GID": "OTM1.RUBP_LTL_TL_001",
                            "RATE_UNIT_BREAK_PROFILE_XID": "RUBP_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "RATE_UNIT_BREAK",
                    "rows": [
                        {
                            "RATE_UNIT_BREAK_GID": "OTM1.RUB_LTL_TL_001",
                            "RATE_UNIT_BREAK_XID": "RUB_LTL_TL_001",
                            "RATE_UNIT_BREAK_PROFILE_GID": "OTM1.RUBP_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "X_LANE",
                    "rows": [{"X_LANE_GID": "OTM1.XLANE_LTL_TL_001", "X_LANE_XID": "XLANE_LTL_TL_001"}],
                },
                {
                    "table_name": "RATE_GEO",
                    "rows": [
                        {
                            "RATE_GEO_GID": "OTM1.RG_LTL_TL_001",
                            "RATE_GEO_XID": "RG_LTL_TL_001",
                            "RATE_OFFERING_GID": "OTM1.RO_LTL_TL_001",
                            "X_LANE_GID": "OTM1.XLANE_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "RATE_GEO_COST_GROUP",
                    "rows": [
                        {
                            "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_LTL_TL_001",
                            "RATE_GEO_COST_GROUP_XID": "RGCG_LTL_TL_001",
                            "RATE_GEO_GID": "OTM1.RG_LTL_TL_001",
                            "RATE_GEO_COST_GROUP_SEQ": 1,
                        }
                    ],
                },
                {
                    "table_name": "RATE_GEO_COST",
                    "rows": [
                        {
                            "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_LTL_TL_001",
                            "RATE_GEO_COST_SEQ": 1,
                            "RATE_UNIT_BREAK_PROFILE_GID": "OTM1.RUBP_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "ACCESSORIAL_CODE",
                    "rows": [
                        {
                            "ACCESSORIAL_CODE_GID": "OTM1.ACC_CODE_LTL_TL_001",
                            "ACCESSORIAL_CODE_XID": "ACC_CODE_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_LTL_TL_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_LTL_TL_001",
                            "COST_CODE_GID": "OTM1.ACC_CODE_LTL_TL_001",
                            "RATE_UNIT_BREAK_PROFILE_GID": "OTM1.RUBP_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "ACCESSORIAL_COST_UNIT_BREAK",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_LTL_TL_001",
                            "RATE_UNIT_BREAK_GID": "OTM1.RUB_LTL_TL_001",
                            "RATE_UNIT_BREAK2_GID": "OTM1.RUB_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "RATE_OFFERING_ACCESSORIAL",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_LTL_TL_001",
                            "RATE_OFFERING_GID": "OTM1.RO_LTL_TL_001",
                            "ACCESSORIAL_CODE_GID": "OTM1.ACC_CODE_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "RATE_GEO_ACCESSORIAL",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_LTL_TL_001",
                            "RATE_GEO_GID": "OTM1.RG_LTL_TL_001",
                            "ACCESSORIAL_CODE_GID": "OTM1.ACC_CODE_LTL_TL_001",
                        }
                    ],
                },
                {
                    "table_name": "RATE_GEO_STOPS",
                    "rows": [
                        {
                            "RATE_GEO_GID": "OTM1.RG_LTL_TL_001",
                            "LOW_STOP": 1,
                            "HIGH_STOP": 3,
                            "PER_STOP_COST": 10,
                        }
                    ],
                },
            ]
        },
        headers=admin_header,
    )
    assert response.status_code == 200

    validation = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    assert validation.status_code == 200
    payload = validation.json()
    assert payload["valid"] is True
    assert payload["status"] == "VALIDATED"
    assert not any(issue["severity"] == "ERROR" for issue in payload["issues"])
    assert not any(
        issue["issue_code"] == "SEQUENCE_DEPENDENCY" and issue["severity"] == "ERROR"
        for issue in payload["issues"]
    )


def test_batch_issues_endpoint_returns_persisted_issues(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/issues",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch["id"]
    assert payload["catalog_macro_object_code"] == "RATE_RECORD"
    assert payload["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert payload["total"] >= 1
