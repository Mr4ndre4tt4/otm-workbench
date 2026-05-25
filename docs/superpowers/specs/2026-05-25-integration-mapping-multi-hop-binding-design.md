# Integration Mapping Multi-Hop Binding Design

**Status:** first backend slice delivered under `OTM-147`
**Date:** 2026-05-25  
**Scope:** explicit backend contract for cross-collection and multi-hop joins in
Integration Mapping preview execution.

## Problem

The current `integration_join_rules` model is intentionally narrow:

```text
source_schema_document_id
left_path
right_path
operator
```

That works for scalar guards and loop-scoped guards where both sides live under
the same source collection.

It is not enough for NDD-like PlannedShipment mappings that need relationships
such as:

```text
ShipmentStop -> ShipUnit -> Release -> ReleaseRefnum
```

The backend must not infer this relationship from path similarity. OTM XML
structures often reuse `Gid/Xid`, `Refnum`, and `Location` shapes, so implicit
path matching can produce plausible but wrong transformations.

## Design Decision

Add an explicit join binding contract instead of overloading
`integration_join_rules`.

The new contract should represent each hop as data:

```text
binding_id
definition_id
source_schema_document_id
name
root_collection_path
target_collection_path
hop_sequence
left_collection_path
left_value_path
right_collection_path
right_value_path
operator
result_alias
status
created_by
```

For the NDD-like case, the authoring model can express:

```text
1. Stop -> ShipUnit
   left_collection_path:  /Transmission/Shipment/ShipmentStop
   left_value_path:       ShipmentStopDetail/ShipUnitGid/Gid/Xid
   right_collection_path: /Transmission/Shipment/ShipUnit
   right_value_path:      ShipUnitGid/Gid/Xid
   result_alias:          stop_ship_unit

2. ShipUnit -> Release
   left_collection_path:  /Transmission/Shipment/ShipUnit
   left_value_path:       ShipUnitContent/ReleaseGid/Gid/Xid
   right_collection_path: /Transmission/Shipment/Release
   right_value_path:      ReleaseGid/Gid/Xid
   result_alias:          ship_unit_release
```

This is deliberately generic and synthetic-data friendly. It does not encode
client identifiers or real project payloads.

## Preview Behavior

Preview execution should:

```text
1. Materialize root collection items.
2. Execute hops in sequence.
3. Keep only matched item indexes and values for each hop.
4. Expose join provenance with collection paths, relative value paths, source
   item indexes, matched target item indexes, operator, and result.
5. Make downstream mapping/aggregation transforms read from an explicit alias,
   not from inferred XML traversal.
```

The minimum executable preview output should add:

```json
{
  "multi_hop_join_provenance": [
    {
      "binding_id": "...",
      "hop_sequence": 1,
      "result_alias": "stop_ship_unit",
      "left_item_path": "/Transmission/Shipment/ShipmentStop[1]/...",
      "right_item_path": "/Transmission/Shipment/ShipUnit[1]/...",
      "operator": "EQ",
      "result": true
    }
  ]
}
```

## Validation

Validation should reject:

```text
- missing source schema document
- paths outside the referenced schema document
- same left/right collection plus same relative value path
- unsupported operator
- duplicate result_alias in one definition
- hop sequence gaps or duplicate hop_sequence inside the same binding
- downstream mappings that reference an alias not produced by a binding
```

## API Shape

Recommended first API:

```text
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/join-bindings
GET  /api/v1/modules/integration-mapping/definitions/{definition_id}/join-bindings
GET  /api/v1/modules/integration-mapping/join-bindings/{binding_id}
```

Payload:

```json
{
  "source_schema_document_id": "schema_source",
  "name": "Stop to release binding",
  "description": "Synthetic PlannedShipment join binding.",
  "root_collection_path": "/Transmission/Shipment/ShipmentStop",
  "target_collection_path": "/Transmission/Shipment/Release",
  "hops": [
    {
      "hop_sequence": 1,
      "left_collection_path": "/Transmission/Shipment/ShipmentStop",
      "left_value_path": "ShipmentStopDetail/ShipUnitGid/Gid/Xid",
      "right_collection_path": "/Transmission/Shipment/ShipUnit",
      "right_value_path": "ShipUnitGid/Gid/Xid",
      "operator": "EQ",
      "result_alias": "stop_ship_unit"
    }
  ],
  "sequence_index": 10
}
```

## Frontend Implication

The existing grouped review table from `OTM-144` should gain a `Join bindings`
group once the backend contract exists.

It should show:

```text
name
root collection
target collection
hop count
aliases
status
blocker
```

No visual canvas is required for the first slice.

## Out Of Scope

```text
- Real OTM transport or live external API calls.
- Client-specific payloads, CNPJ/CPF examples, endpoint credentials, or real
  production values.
- Auto-discovery of OTM relationships from XML paths.
- UI canvas authoring.
```

## Acceptance

```text
- Backend tests create a synthetic two-hop PlannedShipment-like binding.
- Validation rejects invalid paths and duplicate aliases.
- Preview exposes multi_hop_join_provenance.
- Existing Integration Mapping preview and validation tests remain green.
- Documentation marks OTM-145 first slice and binding follow-up separately.
```

## Delivered Slice

`OTM-147` adds the explicit backend contract:

```text
- integration_join_bindings
- integration_join_binding_hops
- POST /definitions/{definition_id}/join-bindings
- GET /definitions/{definition_id}/join-bindings
- GET /join-bindings/{binding_id}
- scalar executable preview provenance under multi_hop_join_provenance
```

`OTM-148` exposes the binding in the staged Rules UI.

`OTM-149` adds the first alias-scoped mapping execution slice. Scalar mappings
can set `transform_config.source_alias` to a join-binding hop alias such as
`ship_unit_release`; preview then reads the mapping value from the matched
joined collection item and emits `source_alias` plus `source_item_path` in
field provenance. Missing aliases block executable preview instead of silently
falling back to global XML traversal.

Remaining accelerator hardening is loop-scoped alias mapping for full
`Entregas[]` materialization and deeper semantic validation.

Verification run:

```text
python -m pytest tests/test_integration_mapping_join_bindings.py -q
python -m pytest tests/test_integration_mapping_*.py -q
python -m ruff check src/otm_workbench/models.py src/otm_workbench/modules/integration_mapping/join_bindings.py src/otm_workbench/modules/integration_mapping/preview.py src/otm_workbench/modules/integration_mapping/routes.py tests/test_integration_mapping_join_bindings.py
```
