def ltl_tl_rate_stack_tables() -> list[dict[str, object]]:
    return [
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
            "rows": [{"RATE_GEO_GID": "OTM1.RG_LTL_TL_001", "LOW_STOP": 1, "HIGH_STOP": 3, "PER_STOP_COST": 10}],
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
    ]
