from sqlalchemy import inspect

from otm_workbench.models import IntegrationEnrichmentStep, IntegrationEnrichmentSubStep
from tests.test_integration_mapping_mappings import create_schema_document, create_source_and_target_documents


def enrichment_payload(source, intermediate, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "response_schema_document_id": intermediate["id"],
        "name": "Synthetic carrier enrichment",
        "description": "Metadata-only enrichment call for synthetic payloads.",
        "step_type": "SINGLE",
        "key_template": "{shipment_gid}",
        "key_source_fields": ["/Transmission/Shipment/ShipmentGid"],
        "response_field_mappings": [
            {
                "response_path": "$.location.locationName",
                "output_field": "carrier_name_enriched",
                "data_type": "String",
                "cardinality": "SCALAR",
            }
        ],
        "on_empty_response": "FAIL",
        "on_error": "FAIL",
        "sequence_index": 30,
    }
    payload.update(overrides)
    return payload


def create_intermediate_document(client, admin_header, definition_id):
    return create_schema_document(
        client,
        admin_header,
        definition_id,
        payload_role="INTERMEDIATE_SAMPLE",
        payload_format="JSON",
        file_name="location_response.json",
        content='{"location":{"locationName":"Synthetic Carrier","status":"ACTIVE"}}',
    )


def test_integration_enrichment_steps_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_enrichment_steps" in table_names
    assert "integration_enrichment_substeps" in table_names
    assert "integration_enriched_fields" in table_names


def test_create_integration_enrichment_step_validates_schema_paths(client, admin_header, db_session):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    step = db_session.get(IntegrationEnrichmentStep, payload["id"])
    assert step is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["source_schema_document_id"] == source["id"]
    assert payload["response_schema_document_id"] == intermediate["id"]
    assert payload["step_type"] == "SINGLE"
    assert payload["key_source_fields"] == ["/Transmission/Shipment/ShipmentGid"]
    assert payload["response_field_mappings"][0]["output_field"] == "carrier_name_enriched"
    assert payload["status"] == "ACTIVE"
    assert "Synthetic Carrier" not in str(payload)


def test_list_enriched_fields_publishes_step_response_mappings(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enriched-fields",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    field = payload["items"][0]
    assert field["definition_id"] == definition["id"]
    assert field["enrichment_step_id"] == created.json()["id"]
    assert field["name"] == "carrier_name_enriched"
    assert field["response_path"] == "$.location.locationName"
    assert field["cardinality"] == "SCALAR"
    assert field["source_trace"]["step_name"] == "Synthetic carrier enrichment"


def test_create_enrichment_substep_publishes_substep_enriched_field(client, admin_header, db_session):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/enrichment-steps/{created.json()['id']}/substeps",
        json={
            "name": "Synthetic chained location detail",
            "response_schema_document_id": intermediate["id"],
            "request_path_template": "/locations/{shipment_gid}",
            "request_key_bindings": {"shipment_gid": "/Transmission/Shipment/ShipmentGid"},
            "response_field_mappings": [
                {
                    "response_path": "$.location.status",
                    "output_field": "carrier_status_enriched",
                    "data_type": "String",
                    "cardinality": "SCALAR",
                }
            ],
            "sequence_index": 2,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    substep = db_session.get(IntegrationEnrichmentSubStep, payload["id"])
    assert substep is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["enrichment_step_id"] == created.json()["id"]
    assert payload["response_field_mappings"][0]["output_field"] == "carrier_status_enriched"

    fields = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enriched-fields",
        headers=admin_header,
    )
    assert fields.status_code == 200
    names = {item["name"] for item in fields.json()["items"]}
    assert {"carrier_name_enriched", "carrier_status_enriched"} <= names


def test_enrichment_readiness_and_step_validation_are_backend_owned(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    validation = client.post(
        f"/api/v1/modules/integration-mapping/enrichment-steps/{created.json()['id']}/validate",
        headers=admin_header,
    )
    readiness = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-readiness",
        headers=admin_header,
    )

    assert validation.status_code == 200
    assert validation.json()["ready"] is True
    assert validation.json()["blockers"] == []
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is True
    assert readiness.json()["step_count"] == 1
    assert readiness.json()["enriched_field_count"] == 1


def test_update_enrichment_step_republishes_enriched_fields(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.patch(
        f"/api/v1/modules/integration-mapping/enrichment-steps/{created.json()['id']}",
        json=enrichment_payload(
            source,
            intermediate,
            name="Synthetic carrier enrichment updated",
            response_field_mappings=[
                {
                    "response_path": "$.location.status",
                    "output_field": "carrier_status_enriched",
                    "data_type": "String",
                    "cardinality": "SCALAR",
                }
            ],
            sequence_index=7,
        ),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Synthetic carrier enrichment updated"
    assert payload["sequence_index"] == 7
    assert payload["response_field_mappings"][0]["output_field"] == "carrier_status_enriched"

    fields = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enriched-fields",
        headers=admin_header,
    )
    assert fields.status_code == 200
    assert fields.json()["total"] == 1
    assert fields.json()["items"][0]["name"] == "carrier_status_enriched"


def test_reorder_enrichment_steps_updates_backend_sequence(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    first = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate, name="Synthetic first step", sequence_index=10),
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(
            source,
            intermediate,
            name="Synthetic second step",
            response_field_mappings=[
                {
                    "response_path": "$.location.status",
                    "output_field": "carrier_status_enriched",
                    "data_type": "String",
                    "cardinality": "SCALAR",
                }
            ],
            sequence_index=20,
        ),
        headers=admin_header,
    )
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps/reorder",
        json={"items": [{"id": second.json()["id"], "sequence_index": 1}, {"id": first.json()["id"], "sequence_index": 2}]},
        headers=admin_header,
    )
    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [second.json()["id"], first.json()["id"]]
    assert [item["id"] for item in listing.json()["items"]] == [second.json()["id"], first.json()["id"]]


def test_retire_enrichment_step_returns_impact_summary(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.delete(
        f"/api/v1/modules/integration-mapping/enrichment-steps/{created.json()['id']}",
        headers=admin_header,
    )
    readiness = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retired"] is True
    assert payload["impact"]["enriched_fields_retired"] == 1
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is False
    assert readiness.json()["step_count"] == 0
