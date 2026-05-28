# GUI Catalog Core Route Separation Completion Review

**Status:** verified for current route-separation scope
**Date:** 2026-05-26
**Scope:** Catalog Core hub, macro-object detail, table explorer/detail,
reference options, and schema guidance route separation.

## 1. Purpose

Record the evidence that Catalog Core moved from a dense shared inspector into
clear route-level catalog utilities with visible return paths, backend-owned
contracts, browser QA screenshots, and direct route recovery.

This review closes the 2026-05-26 Catalog Core route-separation slice tracked
through `GUI_CATALOG_CORE_ROADMAP_SPEC.md`. It does not make Catalog an authoring
or metadata-admin surface.

## 2. Route Inventory

Delivered Catalog routes:

```text
/catalog
/catalog/macro-objects/:macroObjectCode
/catalog/tables
/catalog/tables/:tableName
/catalog/reference-options
/catalog/schema-guidance
```

Each route-level drill-down has a visible `Back` action. The hub now stays
compact: metrics, utility links, validation, and macro-object navigation live on
the hub, while table detail, reference lookup, schema guidance, and macro-object
inspection live on their own screens.

## 3. Delivered UX Decisions

The redesign now separates the main Catalog jobs:

```text
Catalog hub:
  find macro objects, open Catalog utilities, and run compact validation.

Macro-object detail:
  inspect one macro object's tables, load plan, Data Dictionary checks, and
  schema links.

Table explorer:
  search OTM Data Dictionary tables and inspect table columns on a route-level
  detail screen.

Reference options:
  browse backend-owned reference values in the active domain scope and validate
  reference values next to the lookup task.

Schema guidance:
  inspect backend-owned readiness, envelope roots, macro roots, selected XML
  paths, and macro-object schema readiness.
```

The UI keeps Catalog readable for implementation work without making the hub a
wall of every possible backend panel.

## 4. Backend Contract Alignment

The route separation keeps backend ownership for:

```text
macro-object labels, categories, load order, table counts, and allowed methods
macro-object tables, load plan, Data Dictionary cross-checks, and schema links
Data Dictionary table search, table detail, and table columns
table, column, and reference validation results and severity
reference option allowed domain scope and option values
schema guidance readiness, root roles, indexed paths, and source-safe metadata
```

The frontend does not infer OTM table validity, column validity, reference
visibility, schema readiness, or source file paths. Schema-pack creation and
indexing remain admin/backend-owned and are only used by browser QA through
synthetic local data.

## 5. QA Evidence

Frontend contract evidence:

```text
npm run qa:functional:catalog
npm test -- src/app/App.test.tsx
```

Recent result:

```text
6 passed for qa:functional:catalog
21 passed for App.test.tsx
```

Backend/API evidence:

```text
python -m pytest tests/test_catalog_core.py tests/test_reference_catalog.py tests/test_catalog_schema_packs.py
```

Recent result:

```text
46 passed
```

Browser and build evidence:

```text
npm run qa:functional:catalog:browser
npm run build
git diff --check
```

Recent result:

```text
catalog browser journey passed against local FastAPI + Vite
production build passed
git diff --check passed with CRLF normalization warnings only
```

Known non-failing warning from the current harness:

```text
Vite prints the existing chunk-size warning after build because the current app
bundle is larger than the default 500 kB advisory threshold.
```

## 6. Screenshot Evidence

Current screenshot evidence is stored under `output/gui-qa/catalog/`:

```text
01-catalog-hub.png
02-rate-record-detail.png
03-rate-record-route-detail.png
04-table-validation-error.png
05-reference-validation-error.png
06-macro-switch-recovery.png
07-table-explorer.png
08-table-detail.png
09-reference-options.png
10-reference-options-validation-error.png
11-schema-guidance.png
12-schema-guidance-paths.png
```

The screenshots use synthetic local data only. No real client data, credentials,
local customer paths, or production identifiers are used.

## 7. Happy, Negative, Out-Of-Order, And Recovery Coverage

Covered:

```text
hub load with compact utility links
macro-object row click into route-level detail and Back to Catalog recovery
direct URL recovery for /catalog/macro-objects/RATE_RECORD
table explorer search and route-level table detail with Back to Tables
backend-owned table validation error for blocked transactional usage
backend-owned column validation info result
reference options route with allowed domain scope and backend option list
reference validation error on hub and on the reference-options route
schema guidance route with synthetic schema-pack indexing, root selection, and
indexed path inspection
macro-object switch recovery clearing stale validation state
validation reset recovery back to known synthetic defaults
route leave/return recovery through Project Cockpit and Catalog navigation
browser console and HTTP failure checks during the Catalog journey
```

## 8. Remaining Explicit Follow-Up Scope

The following are not blockers for the current route-separation completion
review:

```text
schema guidance query parameter deep-linking to a selected root
clickable macro-object readiness rows from schema guidance back to macro detail
column reference metadata prefill into /catalog/reference-options
copy-to-clipboard actions for client-safe macro codes, table names, and XML
paths
governed admin UI for schema-pack import/indexing
backend pagination/virtualization if Catalog roots, paths, or tables grow large
```

These should remain separate Linear/GitHub follow-ups when prioritized.

## 9. Completion Decision

The current Catalog Core route-separation slice is complete for the implemented
scope. The final verification commands above were rerun on 2026-05-26 and
passed. Linear `OTM-90` and GitHub PR #182 were updated with this evidence.

The next module-planning step can move beyond Catalog route separation. If the
next cycle stays inside Catalog, it should be explicit hardening rather than
completion catch-up.
