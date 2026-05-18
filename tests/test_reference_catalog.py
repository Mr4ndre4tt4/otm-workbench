from otm_workbench.database import Base
from otm_workbench.models import ReferenceFieldPolicy, ReferenceObject
from otm_workbench.reference.services import (
    ReferenceContext,
    list_reference_options,
    validate_reference_value,
)


def test_reference_catalog_tables_are_registered():
    table_names = set(Base.metadata.tables)

    assert "reference_object_types" in table_names
    assert "reference_objects" in table_names
    assert "reference_field_policies" in table_names
    assert "reference_import_batches" in table_names
    assert "otm_table_definitions" in table_names
    assert "otm_table_columns" in table_names
    assert "otm_table_foreign_keys" in table_names
    assert "otm_load_sequences" in table_names
    assert "otm_csv_contracts" in table_names


def test_reference_options_are_filtered_by_public_and_profile_domain(db_session):
    db_session.add_all(
        [
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="PUBLIC.RS_STD",
                xid="RS_STD",
                domain_name="PUBLIC",
                display_name="Standard",
            ),
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="OTM1.RS_EXP",
                xid="RS_EXP",
                domain_name="OTM1",
                display_name="Express",
            ),
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="OTM2.RS_OTHER",
                xid="RS_OTHER",
                domain_name="OTM2",
                display_name="Other",
            ),
        ]
    )
    db_session.commit()

    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id="profile_otm1",
        domain_name="OTM1",
        can_view_all_domains=False,
    )
    options = list_reference_options(db_session, context, "RATE_SERVICE")

    assert [item.gid for item in options] == ["PUBLIC.RS_STD", "OTM1.RS_EXP"]


def test_view_all_domains_context_can_see_all_domains(db_session):
    db_session.add_all(
        [
            ReferenceObject(
                object_type="CURRENCY",
                gid="PUBLIC.USD",
                xid="USD",
                domain_name="PUBLIC",
                display_name="US Dollar",
            ),
            ReferenceObject(
                object_type="CURRENCY",
                gid="OTM2.BRL",
                xid="BRL",
                domain_name="OTM2",
                display_name="Brazilian Real",
            ),
        ]
    )
    db_session.commit()

    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id="profile_dba",
        domain_name="OTM1",
        can_view_all_domains=True,
    )
    options = list_reference_options(db_session, context, "CURRENCY")

    assert [item.gid for item in options] == ["OTM2.BRL", "PUBLIC.USD"]


def test_must_exist_policy_returns_error_when_missing(db_session):
    db_session.add(
        ReferenceFieldPolicy(
            module_id="rates",
            field_name="currency_gid",
            object_type="CURRENCY",
            policy="MUST_EXIST",
            severity_when_missing="ERROR",
            allow_manual_value=False,
        )
    )
    db_session.commit()

    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id="profile_otm1",
        domain_name="OTM1",
        can_view_all_domains=False,
    )
    result = validate_reference_value(db_session, context, "rates", "currency_gid", "OTM1.MISSING")

    assert result.valid is False
    assert result.severity == "ERROR"
    assert result.policy == "MUST_EXIST"


def test_free_text_policy_accepts_missing_value(db_session):
    db_session.add(
        ReferenceFieldPolicy(
            module_id="rates",
            field_name="rate_geo_gid",
            object_type="RATE_GEO",
            policy="FREE_TEXT",
            severity_when_missing="INFO",
            allow_manual_value=True,
        )
    )
    db_session.commit()

    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id="profile_otm1",
        domain_name="OTM1",
        can_view_all_domains=False,
    )
    result = validate_reference_value(
        db_session,
        context,
        "rates",
        "rate_geo_gid",
        "OTM1.NEW_RATE_GEO",
    )

    assert result.valid is True
    assert result.severity == "INFO"
    assert result.policy == "FREE_TEXT"


def test_reference_import_and_options_api_filters_domains(client, admin_header):
    imported = client.post(
        "/api/v1/reference/import-batches",
        json={
            "source_type": "json",
            "source_description": "synthetic seed",
            "records": [
                {
                    "object_type": "RATE_SERVICE",
                    "gid": "PUBLIC.RS_STD",
                    "xid": "RS_STD",
                    "domain_name": "PUBLIC",
                    "display_name": "Standard",
                },
                {
                    "object_type": "RATE_SERVICE",
                    "gid": "OTM1.RS_EXP",
                    "xid": "RS_EXP",
                    "domain_name": "OTM1",
                    "display_name": "Express",
                },
                {
                    "object_type": "RATE_SERVICE",
                    "gid": "OTM2.RS_OTHER",
                    "xid": "RS_OTHER",
                    "domain_name": "OTM2",
                    "display_name": "Other",
                },
            ],
        },
        headers=admin_header,
    )
    assert imported.status_code == 200
    assert imported.json()["records_inserted"] == 3

    response = client.get(
        "/api/v1/reference/options?object_type=RATE_SERVICE&domain_name=OTM1",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert [item["gid"] for item in response.json()["items"]] == [
        "PUBLIC.RS_STD",
        "OTM1.RS_EXP",
    ]


def test_reference_validate_api_uses_policy(client, admin_header):
    response = client.post(
        "/api/v1/reference/validate",
        json={
            "module_id": "rates",
            "field_name": "currency_gid",
            "value": "OTM1.MISSING",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["severity"] == "ERROR"


def test_rate_offering_duplicate_check_returns_warning(client, admin_header):
    client.post(
        "/api/v1/reference/import-batches",
        json={
            "source_type": "json",
            "source_description": "rate offering seed",
            "records": [
                {
                    "object_type": "RATE_OFFERING",
                    "gid": "OTM1.RO_STD",
                    "xid": "RO_STD",
                    "domain_name": "OTM1",
                    "display_name": "Synthetic Standard Offering",
                    "metadata_json": {
                        "servprov_gid": "OTM1.SERVPROV_A",
                        "transport_mode_gid": "PUBLIC.TL",
                        "rate_service_gid": "OTM1.RS_STD",
                        "equipment_group_profile_gid": "PUBLIC.EQP_DRY",
                        "currency_gid": "PUBLIC.USD",
                    },
                }
            ],
        },
        headers=admin_header,
    )

    response = client.post(
        "/api/v1/modules/rates/reference/rate-offerings/duplicate-check",
        json={
            "servprov_gid": "OTM1.SERVPROV_A",
            "transport_mode_gid": "PUBLIC.TL",
            "rate_service_gid": "OTM1.RS_STD",
            "equipment_group_profile_gid": "PUBLIC.EQP_DRY",
            "currency_gid": "PUBLIC.USD",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "WARNING"
    assert response.json()["candidates"][0]["gid"] == "OTM1.RO_STD"
