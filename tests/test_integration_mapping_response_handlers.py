from sqlalchemy import inspect

from otm_workbench.models import IntegrationResponseHandler
from tests.test_integration_mapping_mappings import create_source_and_target_documents


def response_handler_payload(target, **overrides):
    payload = {
        "target_schema_document_id": target["id"],
        "name": "Accepted delivery response",
        "response_path": "$.status",
        "success_condition": "EQUALS",
        "expected_value": "ACCEPTED",
        "outcome": "SUCCESS",
        "description": "Synthetic response rule for NDD-like acceptance.",
        "sequence_index": 1,
    }
    payload.update(overrides)
    return payload


def create_documents_with_response_status(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    target = create_source_and_target_documents_with_target_status(client, admin_header, definition)
    return definition, source, target


def create_source_and_target_documents_with_target_status(client, admin_header, definition):
    from tests.test_integration_mapping_mappings import create_schema_document

    return create_schema_document(
        client,
        admin_header,
        definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="delivery-response.json",
        content='{"status":"ACCEPTED","header":{"shipmentId":"SYNTHETIC"},"deliveries":[{"sequence":1}]}',
    )


def test_integration_response_handlers_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()
    columns = {column["name"] for column in inspect(db_session.bind).get_columns("integration_response_handlers")}

    assert "integration_response_handlers" in table_names
    assert {
        "definition_id",
        "target_schema_document_id",
        "response_path",
        "success_condition",
        "expected_value",
        "outcome",
    }.issubset(columns)


def test_create_and_list_integration_response_handler_validates_schema_path(client, admin_header, db_session):
    definition, _source, target = create_documents_with_response_status(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/response-handlers",
        json=response_handler_payload(target),
        headers=admin_header,
    )
    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/response-handlers",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    handler = db_session.get(IntegrationResponseHandler, payload["id"])
    assert handler is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["response_path"] == "$.status"
    assert payload["success_condition"] == "EQUALS"
    assert payload["expected_value"] == "ACCEPTED"
    assert payload["outcome"] == "SUCCESS"
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == payload["id"]


def test_create_integration_response_handler_rejects_unknown_response_path(client, admin_header):
    definition, _source, target = create_documents_with_response_status(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/response-handlers",
        json=response_handler_payload(target, response_path="$.missingStatus"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_RESPONSE_HANDLER_PATH_INVALID"


def test_validate_integration_definition_reports_response_handler_issues(client, admin_header, db_session):
    definition, _source, target = create_documents_with_response_status(client, admin_header)
    handler = IntegrationResponseHandler(
        definition_id=definition["id"],
        target_schema_document_id=target["id"],
        name="Broken response handler",
        response_path="$.missingStatus",
        success_condition="EQUALS",
        expected_value="ACCEPTED",
        outcome="SUCCESS",
        description="Synthetic invalid handler.",
        sequence_index=1,
        status="ACTIVE",
        created_by="qa@example.test",
    )
    db_session.add(handler)
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    issues = {(issue["entity_type"], issue["field"], issue["code"]) for issue in payload["issues"]}
    assert ("response_handler", "response_path", "INTEGRATION_VALIDATION_PATH_MISSING") in issues
