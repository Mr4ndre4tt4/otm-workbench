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
6. Create direct mappings for selected header fields.
7. Create a loop from ShipmentStop to Entregas[].
8. Create a join for stop/ship-unit style relationship metadata.
9. Create a mock lookup for destination document metadata.
10. Validate the definition.
11. Generate preview/spec artifacts.
12. Download and inspect the generated preview artifact payload.
```

Evidence screenshot:

```text
var/qa/screenshots/integration_mapping_ndd_ui_qa.png
```

This screenshot is local QA evidence and is not intended to contain real client
data.

## Result

The scenario is now possible as an executable positive slice, not only as
metadata/specification.

Delivered behavior observed through the UI:

```text
- Definition creation works.
- Source and target payload artifact creation works.
- XML/JSON schema parsing works for the simplified synthetic payload.
- Mapping rows can be created from schema node selectors.
- Loop, semantic loop join, multi-hop join binding, alias-backed mappings, and
  loop-scoped lookup metadata can be created.
- Validation passes when referenced paths exist.
- Preview materializes executable synthetic JSON for header fields and
  Entregas[] rows.
- Generated preview artifact can be downloaded and inspected.
- Spec generation succeeds.
- Existing browser functional QA passes against local FastAPI + Vite.
```

The module is now a credible first accelerator for this synthetic NDD-like
slice: it can capture the integration definition, parse samples, author
multi-hop relationship rules, generate executable preview JSON, and explain
field-level provenance. It is not yet complete for the full real-world pattern
because richer transforms, required-field packs, response handling, and negative
browser recovery still need hardening.

## Accelerator Assessment

Current accelerator value:

```text
- Good for capturing integration definitions, systems, endpoints, payload
  samples, parsed schema trees, mapping inventory, and generated specs.
- Useful as a governance/specification cockpit.
- Useful to prevent raw payload/spec material from living only in documents.
- Useful as a first executable test harness for header + Entregas[] mappings
  when the scenario fits the supported transforms and alias model.
```

Current limits:

```text
- Not yet enough to author a complete OTM PlannedShipment -> delivery JSON
  transformation without external interpretation.
- Not yet enough to cover all complex transformations from the reference
  mapping: filtered refnums, date formatting, aggregations, response handling,
  and deeper required target semantics beyond the first backend-owned checklist.
- Negative browser recovery for invalid alias/path authoring is covered by
  `OTM-153`.
```

## UI/UX Findings

1. The staged workflow is better than stacked panels, but the mapping stage is
   still too dense for complex integrations.
2. Source/target schema node selectors show long paths in plain selects. For
   OTM XML paths with repeated `Gid/Xid` structures, this is easy to misread.
3. Earlier QA found that a meaningless join was easy to author because similar
   OTM node paths are hard to distinguish in plain selects. The current browser
   journey uses a semantically valid synthetic loop join, but the selector UX
   still needs a searchable tree/path reviewer for real payloads.
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
  got a first visible scenario-pack checklist in `OTM-154`.
- Executable local preview that materializes synthetic target JSON from
  mappings, loops, joins, lookups, and transforms. First mixed
  header/Entregas[] alias-backed slice delivered by `OTM-152`.
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
    artifact review. `OTM-152` delivered the positive executable artifact
    review; `OTM-153` delivered negative alias/path browser recovery.
11. Expose required target scenario packs in validation and UI. `OTM-154`
    delivered the first backend-owned required target checklist for the
    synthetic NDD-like target JSON.
12. Add backend-owned response handling rules. `OTM-155` delivered persisted
    response handlers, schema-path validation, UI authoring/review, spec output,
    and browser QA for `$.status EQUALS ACCEPTED -> SUCCESS`.
13. Add guided transform config authoring. `OTM-156` delivered Rules-stage
    inputs for `CONSTANT` and `DATE_FORMAT`, while keeping backend validation and
    preview execution as source of truth.
14. Add guided complex transform authoring. `OTM-157` delivered Rules-stage
    inputs for `FILTER_BY_QUALIFIER` and `COUNT_DISTINCT`, with executable
    preview assertions for filtered access key and release count.
15. Add schema search and deterministic mapping suggestions. `OTM-158`
    delivered source/target node search plus an apply-suggestion action that
    fills source path, target path, and transform type without auto-creating a
    mapping.
```

## OTM-152 Evidence

`OTM-152` extended the browser functional script to prove more than artifact
creation. The script now:

```text
- Authors a synthetic PlannedShipment-like XML and external delivery JSON.
- Creates header mapping, Entregas[] loop mapping, multi-hop stop -> ship unit
  -> release join binding, and alias-backed header/Entregas access-key mappings.
- Creates a loop-scoped mock lookup into Entregas[].carrierName.
- Validates and previews the definition.
- Downloads `integration_preview.json`.
- Asserts executable JSON:
  - header.shipmentId = DEMO.SHIPMENT_001
  - header.accessKey = KEY-001
  - deliveries[0].sequence = 1
  - deliveries[0].accessKey = KEY-001
  - deliveries[0].carrierName = Synthetic Carrier
- Asserts field provenance includes source alias `ship_unit_release` for
  `$.deliveries[0].accessKey`.
```

## OTM-153 Evidence

`OTM-153` added the negative recovery path to the same browser journey:

```text
- Creates an isolated alternate synthetic definition.
- Authors a valid multi-hop join binding.
- Intentionally creates an alias-backed mapping where `source_alias` is valid
  but `source_path` is outside the alias collection scope.
- Validates backend blocker:
  `INTEGRATION_VALIDATION_MAPPING_ALIAS_SCOPE_INVALID`.
- Attempts preview and confirms backend blocks it instead of producing stale
  success evidence.
- Removes the invalid mapping through a backend-owned delete action.
- Recreates the mapping with a release-scoped source path.
- Validates and previews again without route reload.
```

## OTM-154 Evidence

`OTM-154` made required target semantics visible instead of hidden in validation
internals:

```text
- Validation now returns a `scenario_pack` object when the definition activates
  the synthetic PlannedShipment -> External Delivery checklist.
- The checklist includes required targets, covered/missing state, coverage
  type, and missing target list.
- The UI renders `Integration mapping required target checklist` in the
  selected definition panel after validation.
- Browser QA creates a separate synthetic scenario definition with
  `EXTERNAL_DELIVERY_NDD`, validates missing targets, then adds mappings/loop
  until the checklist is fully covered without route reload.
```

## OTM-155 Evidence

`OTM-155` closed the response-handling gap for the first Integration Mapping
accelerator slice:

```text
- Backend table/model/API: integration_response_handlers.
- API validates target schema ownership, response_path existence, controlled
  success_condition values, controlled outcome values, and required expected
  value for EQUALS.
- Definition validation checks persisted response handlers so direct DB drift
  is caught before preview/spec.
- Generated markdown specs now include response handling rows without embedding
  raw source/target payloads.
- UI Rules stage can author response handlers and the grouped executable review
  replaces the old empty response-handling placeholder with the real rule.
- Browser QA creates `Accepted delivery response` with
  `$.status EQUALS ACCEPTED -> SUCCESS`, validates grouped review visibility,
  then resets drafts and verifies return-to-empty state.
```

## OTM-156 Evidence

`OTM-156` made transform configuration explicit in the UI instead of implicit in
payload JSON:

```text
- Rules-stage mapping form now exposes `Constant value` when transform_type is
  CONSTANT.
- Rules-stage mapping form now exposes source format, target format, and
  timezone offset when transform_type is DATE_FORMAT.
- Alias source context remains composable with transform_config instead of
  replacing it.
- React functional QA asserts CONSTANT sends `{ value: "ACCEPTED" }` and
  DATE_FORMAT sends `{ source_format, target_format, timezone_offset }`.
- Browser QA creates both mappings against the real backend and validates the
  generated preview artifact:
  - status = ACCEPTED
  - issuedAt = 2026-05-25T10:30:00-03:00
- Reset mapping drafts clears constant/date inputs back to backend-safe defaults.
```

## OTM-157 Evidence

`OTM-157` extended guided transform config authoring to the first complex
mapping cases:

```text
- FILTER_BY_QUALIFIER now has explicit Rules-stage fields for collection path,
  qualifier path, qualifier value, and value path.
- COUNT_DISTINCT now has explicit Rules-stage fields for collection path and
  value path.
- React functional QA asserts the exact backend payloads sent for both
  transform_config shapes.
- Browser QA creates both mappings against the real backend and validates the
  generated preview artifact:
  - header.filteredAccessKey = KEY-001
  - header.releaseCount = 1
- Reset mapping drafts clears the complex transform fields back to empty values.
- The grouped review no longer implies COUNT_DISTINCT itself is pending; only a
  future dedicated aggregation-rule object remains out of scope.
```

## OTM-158 Evidence

`OTM-158` reduced path-hunting friction in the Rules stage:

```text
- Mapping source and target schema node selectors now have dedicated search
  inputs.
- Loaded source/target schema nodes generate deterministic semantic suggestions
  when leaf node names match after normalization, such as
  ShipmentGid -> shipmentId.
- Applying a suggestion fills source_path, target_path, and DIRECT transform
  type; it does not create the mapping automatically.
- Applying a suggestion clears the search inputs so the next mapping is not
  accidentally filtered.
- Schema node selects now expose explicit aria-labels, avoiding ambiguous
  browser automation labels after search inputs were added.
- React and browser QA prove suggestion application, normal create flow,
  return/reset state, and executable preview still work.
```
