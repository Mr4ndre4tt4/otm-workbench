from otm_workbench.models import (
    IntegrationJoinRule,
    IntegrationLookupDefinition,
    IntegrationLoopDefinition,
    IntegrationMapping,
)
from tests.test_integration_mapping_joins import join_payload
from tests.test_integration_mapping_lookups import lookup_payload
from tests.test_integration_mapping_loops import loop_payload
from tests.test_integration_mapping_mappings import (
    create_definition,
    create_schema_document,
    create_source_and_target_documents,
    mapping_payload,
)


def create_full_valid_definition(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    mapping = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(source, target),
        headers=admin_header,
    )
    loop = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )
    join = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source),
        headers=admin_header,
    )
    lookup = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target),
        headers=admin_header,
    )
    assert mapping.status_code == 200
    assert loop.status_code == 200
    assert join.status_code == 200
    assert lookup.status_code == 200
    return definition, source, target


def test_validate_integration_definition_returns_no_issues_for_valid_metadata(client, admin_header):
    definition, _source, _target = create_full_valid_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["definition_id"] == definition["id"]
    assert payload["is_valid"] is True
    assert payload["issue_count"] == 0
    assert payload["issues"] == []


def test_validate_integration_definition_reports_structural_issues(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    rows = [
        IntegrationMapping(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_path="/Transmission/Missing",
            target_path="$.header.shipmentId",
            transform_type="DIRECT",
            description="Invalid synthetic mapping.",
            sequence_index=1,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
        IntegrationLoopDefinition(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_collection_path="/Transmission/Shipment/ShipmentStop",
            target_collection_path="$.missing[]",
            name="Invalid synthetic loop",
            description="Invalid synthetic loop.",
            sequence_index=2,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
        IntegrationJoinRule(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            left_path="/Transmission/Shipment/ShipmentGid",
            right_path="/Transmission/Missing",
            operator="EQ",
            name="Invalid synthetic join",
            description="Invalid synthetic join.",
            sequence_index=3,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
        IntegrationLookupDefinition(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            input_path="/Transmission/Shipment/ShipmentGid",
            output_path="$.missing",
            lookup_type="MOCK",
            name="Invalid synthetic lookup",
            description="Invalid synthetic lookup.",
            mock_response_json='{"shipmentId":"DEMO-SHIPMENT"}',
            sequence_index=4,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
    ]
    db_session.add_all(rows)
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert payload["issue_count"] == 4
    issues = {(issue["entity_type"], issue["field"], issue["code"]) for issue in payload["issues"]}
    assert ("mapping", "source_path", "INTEGRATION_VALIDATION_PATH_MISSING") in issues
    assert ("loop", "target_collection_path", "INTEGRATION_VALIDATION_PATH_MISSING") in issues
    assert ("join", "right_path", "INTEGRATION_VALIDATION_PATH_MISSING") in issues
    assert ("lookup", "output_path", "INTEGRATION_VALIDATION_PATH_MISSING") in issues


def test_validate_integration_definition_reports_semantic_mapping_issues(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    rows = [
        IntegrationMapping(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_path="/Transmission/Shipment/ShipmentGid",
            target_path="$.header.shipmentId",
            transform_type="DIRECT",
            description="First synthetic mapping.",
            sequence_index=1,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
        IntegrationMapping(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_path="/Transmission/Shipment/ShipmentStop/StopSequence",
            target_path="$.header.shipmentId",
            transform_type="DIRECT",
            description="Duplicate target synthetic mapping.",
            sequence_index=2,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
        IntegrationJoinRule(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            left_path="/Transmission/Shipment/ShipmentGid",
            right_path="/Transmission/Shipment/ShipmentGid",
            operator="EQ",
            name="Same path join",
            description="Join with no semantic value.",
            sequence_index=3,
            status="ACTIVE",
            created_by="qa@example.test",
        ),
    ]
    db_session.add_all(rows)
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    issues = {(issue["entity_type"], issue["field"], issue["code"]) for issue in payload["issues"]}
    assert ("mapping", "target_path", "INTEGRATION_VALIDATION_DUPLICATE_TARGET_PATH") in issues
    assert ("join", "right_path", "INTEGRATION_VALIDATION_JOIN_SAME_PATH") in issues


def test_validate_integration_definition_reports_missing_required_targets_for_ndd_pack(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentHeader>"
            "<ShipmentGid><Gid><Xid>SHIP_SYN_001</Xid></Gid></ShipmentGid>"
            "<StartDt><PlannedTime><GLogDate>2026-05-25T10:00:00-03:00</GLogDate></PlannedTime></StartDt>"
            "</ShipmentHeader>"
            "<ShipmentStop><StopSequence>1</StopSequence></ShipmentStop>"
            "</Shipment>"
            "</Transmission>"
        ),
    )
    target = create_schema_document(
        client,
        admin_header,
        definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="external_delivery_ndd.json",
        content=(
            '{"NumeroViagem":"","DataEmissao":"","Entregas":['
            '{"NumeroDocumento":"","ChaveAcesso":""}'
            "]}"
        ),
    )
    db_definition = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}",
        headers=admin_header,
    ).json()
    assert db_definition["code"] == "PS_MAPPING_CRUD"

    # The scenario pack is activated by this code family so generic definitions
    # keep their lightweight MVP0 validation.
    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(
            source,
            target,
            source_path="/Transmission/Shipment/ShipmentHeader/ShipmentGid/Gid/Xid",
            target_path="$.NumeroViagem",
        ),
        headers=admin_header,
    )
    assert response.status_code == 200

    # Direct DB update keeps this focused on validation behavior without adding
    # a dedicated scenario-pack authoring API in this slice.
    from otm_workbench.database import session_scope
    from otm_workbench.models import IntegrationDefinition

    with session_scope() as db:
        row = db.get(IntegrationDefinition, definition["id"])
        row.code = "PS_TO_EXTERNAL_DELIVERY_NDD_REQUIRED"

    validation = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert validation.status_code == 200
    payload = validation.json()
    assert payload["is_valid"] is False
    required_target_issues = [
        issue for issue in payload["issues"] if issue["code"] == "INTEGRATION_VALIDATION_REQUIRED_TARGET_MISSING"
    ]
    missing_paths = {issue["field"] for issue in required_target_issues}
    assert missing_paths == {"$.DataEmissao", "$.Entregas[]", "$.Entregas[].NumeroDocumento", "$.Entregas[].ChaveAcesso"}


def test_validate_integration_definition_reports_lookup_output_without_loop_scope(
    client,
    admin_header,
    db_session,
):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    lookup = IntegrationLookupDefinition(
        definition_id=definition["id"],
        source_schema_document_id=source["id"],
        target_schema_document_id=target["id"],
        input_path="/Transmission/Shipment/ShipmentGid",
        output_path="$.deliveries[].sequence",
        lookup_type="MOCK",
        name="Delivery lookup without loop",
        description="Synthetic lookup into a collection without loop scope.",
        mock_response_json='{"sequence":1}',
        sequence_index=1,
        status="ACTIVE",
        created_by="qa@example.test",
    )
    db_session.add(lookup)
    db_session.commit()

    validation = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert validation.status_code == 200
    payload = validation.json()
    assert payload["is_valid"] is False
    assert (
        "lookup",
        "output_path",
        "INTEGRATION_VALIDATION_LOOKUP_OUTPUT_SCOPE_MISSING",
    ) in {(issue["entity_type"], issue["field"], issue["code"]) for issue in payload["issues"]}


def test_validate_integration_definition_reports_missing_transform_config_for_expression_type(
    client,
    admin_header,
):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(
            source,
            target,
            source_path="/Transmission/Shipment/ShipmentGid",
            target_path="$.header.shipmentId",
            transform_type="DATE_FORMAT",
        ),
        headers=admin_header,
    )
    assert created.status_code == 200

    validation = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert validation.status_code == 200
    payload = validation.json()
    assert payload["is_valid"] is False
    assert payload["readiness"]["specification_ready"] is True
    assert payload["readiness"]["preview_executable"] is False
    assert "INTEGRATION_VALIDATION_TRANSFORM_CONFIG_MISSING" in payload["readiness"]["preview_blockers"]
    assert (
        "mapping",
        "transform_type",
        "INTEGRATION_VALIDATION_TRANSFORM_CONFIG_MISSING",
    ) in {(issue["entity_type"], issue["field"], issue["code"]) for issue in payload["issues"]}


def test_validate_integration_definition_rejects_missing_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/validate",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
