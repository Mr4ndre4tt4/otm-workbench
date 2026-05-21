# GUI Long Label Responsive Contract

**Status:** delivered  
**Branch:** `codex/gui-long-label-responsive-coverage`  
**Linear:** `OTM-71`  
**Scope:** responsive handling for long labels, path-like values, table names, file names, and generated object identifiers.

## 1. Purpose

Module screens will regularly render OTM object names, table names, payload
paths, XML/JSON paths, generated file names, validation codes, and other values
that can be much longer than a typical UI label.

Shared GUI components must preserve layout integrity when those values appear.
The goal is readable wrapping, not clipped or overlapping text.

## 2. Covered Surfaces

The long-label guardrail applies to shared module surfaces:

```text
MetricGrid
ModuleObjectList
SelectedObjectPanel
DetailList
ArtifactList
BlockerPanel
OperationalPanel
ActivityRow
StatusChip
ActionBar
ContextSummary
ReadinessPanel
```

Module screens should inherit the behavior from shared CSS instead of adding
module-local truncation rules.

## 3. Values That Must Wrap Safely

These values must be safe at desktop, compact, and mobile widths:

```text
- module object titles
- module object subtitles
- selected object titles
- selected object fields
- metric labels and values
- table names
- OTM table/object codes
- payload artifact file names
- generated artifact file names
- source XML paths
- target JSON paths
- schema root names
- mapping target paths
- blocker codes and messages
- action labels
- status labels
```

## 4. CSS Rule

Shared text-heavy surfaces must use wrapping rules that allow long unbroken
strings to wrap inside their container:

```text
overflow-wrap: anywhere;
word-break: normal;
min-width: 0;
```

Use this at shared component/layout level. Do not add page-specific CSS for one
module unless an exception is documented.

## 5. Layout Rule

Reusable grids that contain user/backend labels should keep flexible columns:

```text
minmax(0, 1fr)
```

Mobile breakpoints should collapse text-heavy multi-column rows to one column
before the content overlaps. The existing responsive layer owns those
breakpoints.

## 6. Truncation Rule

Do not use truncation as the default for operational labels.

Allowed only with an approved exception:

```text
- single-line breadcrumb chips
- intentionally compact navigation labels
- dense data-table cells with full value available through an accessible detail
```

If truncation is introduced later, it must preserve keyboard/screen-reader
access to the full value.

## 7. Client-Safe Fixtures

Long-label tests must use synthetic values only.

Useful synthetic examples:

```text
XLANE_RATE_GEO_COST_GROUP_WITH_SYNTHETIC_EXTRA_LONG_IDENTIFIER_FOR_RESPONSIVE_CHECK
/GLogXMLElement/PlannedShipment/Shipment/ShipmentHeader/StartDt/PlannedTime
$.viagem.entregas[0].documento.chaveAcessoSintetica
synthetic_order_release_export_with_extra_long_file_name_for_responsive_checks.xml
```

Do not use real client names, identifiers, payload bodies, document numbers,
local file paths, CNPJ, CPF, secrets, or screenshots from customer data.

## 8. Browser QA Boundary

This contract is a code and documentation guardrail. It does not claim visual pixel evidence.

Browser visual QA is accepted only when a branch-specific browser run,
screenshot, or comparable visual QA artifact exists. OTM-77 and OTM-78 now
provide Playwright fallback evidence for shell/Project Cockpit and Rates Studio.
Other modules and the internal gallery still need their own visual QA evidence.

## 9. Guardrails

This contract is enforced by:

```text
frontend/tests/guiLongLabelResponsiveContract.test.ts
frontend/tests/cssLayerOwnership.test.ts
frontend/tests/guiSyntheticFixturesContract.test.ts
```

The tests keep this contract discoverable and verify that shared CSS contains
the long-label wrapping rule.

## 10. Acceptance Criteria

This contract is accepted when:

```text
- the contract is linked from GUI_CONTRACT_INDEX.md
- the contract is linked from GUI_MVP1_PLAN.md
- covered shared surfaces are listed
- long path-like values are listed
- shared CSS includes the wrapping guardrail
- client-safe fixture rules are explicit
- browser visual QA boundary and current fallback evidence are documented
```
