# Integration Mapping Studio NDD UI QA

**Date:** 2026-05-25  
**Scope:** browser UI attempt to recreate a synthetic version of the NDD-style
PlannedShipment XML to external delivery JSON integration.  
**Data policy:** synthetic payloads only. No real customer identifiers, CNPJ,
CPF, endpoint credentials, raw customer files, or production payload values were
copied into the repository.

## Scenario Attempted

The UI flow created a synthetic definition:

```text
OTM PlannedShipment XML
-> External delivery JSON
```

The browser journey covered:

```text
1. Open Integration Mapping Studio in the shared Workbench shell.
2. Create a synthetic Integration Definition.
3. Paste a synthetic PlannedShipment-like XML payload.
4. Paste a synthetic external delivery JSON target payload.
5. Parse both payloads into schema documents and schema nodes.
6. Create direct/date mappings for selected header fields.
7. Create a loop from ShipmentStop to Entregas[].
8. Create a join for stop/ship-unit style relationship metadata.
9. Create a mock lookup for destination document metadata.
10. Validate the definition.
11. Generate preview/spec artifacts.
```

Evidence screenshot:

```text
var/qa/screenshots/integration_mapping_ndd_ui_qa.png
```

This screenshot is local QA evidence and is not intended to contain real client
data.

## Result

The scenario is possible only as a metadata/specification exercise today.

Delivered behavior observed through the UI:

```text
- Definition creation works.
- Source and target payload artifact creation works.
- XML/JSON schema parsing works for the simplified synthetic payload.
- Mapping rows can be created from schema node selectors.
- Loop, join, and lookup metadata can be created.
- Validation passes when referenced paths exist.
- Spec generation succeeds.
- Existing browser functional QA passes against local FastAPI + Vite.
```

The module is not yet able to recreate the full NDD-style integration as a
complete accelerator because preview output remains metadata-only and the
authoring model lacks several first-class transformation concepts from the real
functional pattern.

## Accelerator Assessment

Current accelerator value:

```text
- Good for capturing integration definitions, systems, endpoints, payload
  samples, parsed schema trees, mapping inventory, and generated specs.
- Useful as a governance/specification cockpit.
- Useful to prevent raw payload/spec material from living only in documents.
```

Current limits:

```text
- Not yet enough to author a complete OTM PlannedShipment -> delivery JSON
  transformation without external interpretation.
- Not yet enough to prove generated target payload correctness.
- Not yet enough to reduce complex mapping effort materially for loops, joins,
  filtered refnums, aggregations, and lookups.
```

## UI/UX Findings

1. The staged workflow is better than stacked panels, but the mapping stage is
   still too dense for complex integrations.
2. Source/target schema node selectors show long paths in plain selects. For
   OTM XML paths with repeated `Gid/Xid` structures, this is easy to misread.
3. During the QA run, a join could be created with the same left and right path
   because the UI made similar node options hard to distinguish.
4. Validation only verifies that paths exist and catalogs are active. It does
   not validate semantic usefulness, for example whether a join relates two
   different structures or whether a lookup output belongs inside the right
   loop scope.
5. Success feedback is overwritten by later actions. After validate, preview,
   and spec, the user loses an easy timeline of what passed.
6. The selected-object panel is useful, but it is not enough for reviewing a
   large integration. Users need a review stage that summarizes completeness by
   header fields, delivery loop fields, lookups, joins, aggregations, response
   handling, and test coverage.

## Functional Gaps

The NDD-style scenario requires these capabilities before the module can be
called complete for this class of integration:

```text
- FILTER_BY_QUALIFIER transform for refnum qualifier/value extraction.
  First backend slice delivered in `OTM-145`.
- COUNT_DISTINCT or COUNT_BY_FILTER for QtdNFe/QtdCTe.
  COUNT_DISTINCT first backend slice delivered in `OTM-145`.
- FORMAT_DATE_ISO8601 with expression/config fields, not just transform code.
- LOOKUP_VALUE from mock/external lookup response into target fields.
- DEFAULT_IF_EMPTY and controlled constant values with visible expression UI.
- Loop-scoped target mappings, so Entregas[] field mappings are clearly tied to
  the ShipmentStop loop.
- Multi-hop join authoring for ShipmentStop -> ShipUnit -> Release.
  Backend contract delivered in `OTM-147`; staged Rules UI authoring and grouped
  review delivered in `OTM-148`; scalar downstream alias-scoped mapping
  delivered in `OTM-149`; loop-scoped alias mapping for `Entregas[]` delivered
  in `OTM-150`.
- Semantic validation for joins, loop scope, duplicate target fields, missing
  required target fields, and transform configuration. `OTM-151` delivered
  missing/out-of-scope alias blockers; fuller scenario required-field semantics
  remain open.
- Executable local preview that materializes synthetic target JSON from
  mappings, loops, joins, lookups, and transforms.
- Response handling model for success/error paths.
```

## Roadmap Steps

Recommended next backlog sequence:

```text
1. Add a scenario pack for PlannedShipment -> External Delivery JSON with
   synthetic source/target samples and required target field checklist.
2. Replace plain schema selects with searchable tree pickers that show path,
   parent context, node type, and sample-safe metadata.
3. Add mapping review table grouped by Header, Entregas loop, Lookups, Joins,
   Aggregations, and Response Handling. First slice delivered in `OTM-144`:
   the Rules stage now shows a grouped executable review using current
   mappings, loops, joins, lookups, validation readiness, and explicit future
   scope rows for aggregations and response handling.
4. Add expression/config UI for CONSTANT, CONCAT, DATE_FORMAT and future
   transform types.
5. Extend transform catalog with FILTER_BY_QUALIFIER, COUNT_DISTINCT,
   LOOKUP_VALUE, DEFAULT_IF_EMPTY, FORMAT_DATE_ISO8601. `OTM-145` delivered
   FILTER_BY_QUALIFIER and COUNT_DISTINCT for scalar executable preview.
6. Add loop-scoped field mapping support for target collections.
7. Add multi-hop join metadata and validation. Backend slice delivered in
   `OTM-147`; staged Rules UI authoring/review delivered in `OTM-148`; scalar
   alias-scoped downstream mapping delivered in `OTM-149`; loop-scoped alias
   mapping delivered in `OTM-150`.
8. Harden validation to catch same-path joins, duplicate target paths, missing
   required target fields, invalid lookup output scope, and transform config
   gaps. `OTM-151` delivered missing/out-of-scope alias validation and UI alias
   source selection.
9. Implement executable synthetic preview that renders target JSON and shows
   field-level provenance.
10. Add browser QA for the full NDD-like synthetic scenario, including wrong
    path selection, reset/recovery, definition switching, and generated
    artifact review.
```
