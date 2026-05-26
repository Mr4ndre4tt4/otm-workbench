# GUI Catalog Core Roadmap Specification

**Status:** route separation delivered and completion-reviewed
**Date:** 2026-05-26  
**Scope:** `/catalog` OTM Catalog Core route-level redesign.

## 1. Problem Statement

Catalog Core is now a shared source for Master Data, Rates, Integration
Mapping, Assets, Order Release Generator, Load Plan, and schema-pack guidance.
The current `/catalog` screen proves backend contracts, but it still behaves
like a dense inspector: macro-object list, metrics, schema guidance, validation
forms, tables, load plan, and cross-checks all compete on one route.

The next Catalog Core UI must make the user's question obvious:

```text
What OTM object am I looking at?
Which tables and dependencies belong to it?
Which official XML/schema paths guide integration work?
Can this table, column, or reference value be used safely?
What route should I open next?
```

## 2. Design Decision

Use a route-level catalog explorer:

```text
/catalog
  Catalog hub and macro-object library.

/catalog/macro-objects/:macroObjectCode
  Macro-object detail with tables, dependencies, load sequence, Data Dictionary
  cross-check, schema links, and next-action guidance.

/catalog/tables
  Data Dictionary table search and validation workspace.

/catalog/tables/:tableName
  Table detail with columns, date/reference metadata, dependency hints, and
  module usage links.

/catalog/reference-options
  Reference option browser and validation workspace.

/catalog/schema-guidance
  Schema pack/root/path readiness and inspector.
```

Keep Catalog Core read-only for business metadata unless a backend-owned
schema-pack or metadata-admin action explicitly exists.

## 3. Core Navigation Map

```text
Catalog hub
  -> Macro object detail
      -> Table detail
      -> Schema guidance filtered by macro object/root
      -> Load Plan package sequence consumers
  -> Table explorer
      -> Table detail
      -> Column validation result
  -> Reference options
      -> Object type/domain-filtered options
      -> Reference validation result
  -> Schema guidance
      -> Root detail/path inspector
      -> Macro-object schema links
```

The hub should stay compact: one search/list region, one selected "recent or
recommended" summary, and a small validation/action surface. Deep inspection
belongs to route-level screens.

## 4. Global UX Rules

- Backend owns macro-object labels, status, counts, load sequence, schema
  guidance roles, validation results, reference policy, and Data Dictionary
  truth.
- Do not display local Data Dictionary filesystem paths.
- Do not display real client domains, reference values, endpoint names, or
  credentials in docs, tests, screenshots, seeds, or fixtures.
- Long table, column, root-path, and XML-path labels must wrap or truncate
  inside fixed-width list rows without resizing the screen.
- Every route-level detail screen must have a visible return path.
- Validation panels must show the backend error/blocker and keep the recovery
  action next to the form that caused it.
- Schema-pack creation/indexing remains admin-only and hidden from normal
  Catalog users until the backend exposes a governed UI contract.

## 5. Screen Specs

### `/catalog`

Purpose:

```text
Find the right macro object or choose the right Catalog utility.
```

Loads:

```text
GET /api/v1/catalog/macro-objects
GET /api/v1/catalog/schema-guidance/readiness
```

Clicks:

```text
Macro-object row -> /catalog/macro-objects/:macroObjectCode
Table explorer -> /catalog/tables
Reference options -> /catalog/reference-options
Schema guidance -> /catalog/schema-guidance
```

Do not place full table lists, full schema path lists, or all validation forms
on the hub.

### `/catalog/macro-objects/:macroObjectCode`

Purpose:

```text
Inspect one macro object's OTM tables, dependencies, load sequence, and schema
links.
```

Loads:

```text
GET /api/v1/catalog/macro-objects/{macro_object_code}
GET /api/v1/catalog/macro-objects/{macro_object_code}/tables
GET /api/v1/catalog/macro-objects/{macro_object_code}/load-plan
GET /api/v1/catalog/macro-objects/{macro_object_code}/data-dictionary-cross-check
GET /api/v1/catalog/macro-objects/{macro_object_code}/schema-links
```

Clicks:

```text
Back to Catalog -> /catalog
Table row -> /catalog/tables/:tableName
Schema link -> /catalog/schema-guidance?root=<schemaRootId>
Use in Master Data / Rates / Integration Mapping -> target module route when
the backend marks the macro object as supported for that module.
```

Actions:

```text
Refresh detail
Copy client-safe macro object code
```

No editing or deletion on this route.

### `/catalog/tables`

Purpose:

```text
Search OTM Data Dictionary tables and validate whether a table is suitable for
the intended usage.
```

Loads:

```text
GET /api/v1/catalog/tables?query=&limit=
```

Actions:

```text
POST /api/v1/catalog/validate/table
```

Clicks:

```text
Table row -> /catalog/tables/:tableName
Back to Catalog -> /catalog
```

Negative states:

```text
unknown table
known table that is blocked for the selected usage
empty search result
```

### `/catalog/tables/:tableName`

Purpose:

```text
Inspect one Data Dictionary table and its columns before another module uses it.
```

Loads:

```text
GET /api/v1/catalog/tables/{table_name}
GET /api/v1/catalog/tables/{table_name}/columns
```

Actions:

```text
POST /api/v1/catalog/validate/column
```

Clicks:

```text
Back to table explorer -> /catalog/tables
Column reference metadata -> /catalog/reference-options with object type and
field draft prefilled when available.
```

### `/catalog/reference-options`

Purpose:

```text
Browse and validate backend-owned reference options in the active project,
profile, environment, and domain context.
```

Loads:

```text
GET /api/v1/catalog/reference/options
```

Actions:

```text
POST /api/v1/catalog/validate/reference
```

Negative states:

```text
value not found
value outside active domain visibility
field without a reference policy
empty option list for the selected object type/domain
```

### `/catalog/schema-guidance`

Purpose:

```text
Inspect official schema-pack readiness, root roles, XML paths, and macro-object
schema links without exposing local schema files.
```

Loads:

```text
GET /api/v1/catalog/schema-guidance/readiness
GET /api/v1/catalog/schema-roots?schema_guidance_role=
GET /api/v1/catalog/schema-roots/{schema_root_id}/paths?query=
GET /api/v1/catalog/schema-packs
GET /api/v1/catalog/schema-packs/{schema_pack_id}
GET /api/v1/catalog/schema-packs/{schema_pack_id}/service-operations
```

Clicks:

```text
Schema root row -> root path inspector on the same route
Macro-object link -> /catalog/macro-objects/:macroObjectCode
Path row -> copy client-safe XML path and metadata
```

Admin actions such as schema-pack indexing require a separate governed admin
route or deliberate modal with permissions, audit, and safety copy.

## 6. Backend Contract Alignment

Current ready contracts:

```text
GET  /api/v1/catalog/health
GET  /api/v1/catalog/tables
GET  /api/v1/catalog/tables/{table_name}
GET  /api/v1/catalog/tables/{table_name}/columns
GET  /api/v1/catalog/reference/options
GET  /api/v1/catalog/macro-objects
GET  /api/v1/catalog/macro-objects/{macro_object_code}
GET  /api/v1/catalog/macro-objects/{macro_object_code}/tables
GET  /api/v1/catalog/macro-objects/{macro_object_code}/load-plan
GET  /api/v1/catalog/macro-objects/{macro_object_code}/data-dictionary-cross-check
GET  /api/v1/catalog/macro-objects/{macro_object_code}/schema-links
GET  /api/v1/catalog/schema-guidance/readiness
GET  /api/v1/catalog/schema-packs
GET  /api/v1/catalog/schema-packs/{schema_pack_id}
GET  /api/v1/catalog/schema-packs/{schema_pack_id}/service-operations
GET  /api/v1/catalog/schema-roots
GET  /api/v1/catalog/schema-roots/{schema_root_id}/paths
POST /api/v1/catalog/validate/table
POST /api/v1/catalog/validate/column
POST /api/v1/catalog/validate/reference
```

Admin-only or future UI-governed contract:

```text
POST /api/v1/catalog/schema-packs
POST /api/v1/catalog/schema-packs/{schema_pack_id}/index
```

## 7. QA Journeys

Layer 1 React:

```text
npm run qa:functional:catalog
```

Must cover:

```text
hub load
macro-object detail route
table explorer route
table detail route
reference options route
schema guidance route
invalid table/column/reference recovery
macro-object switch clearing stale validation results
route leave/return recovery
```

Layer 2 browser:

```text
npm run qa:functional:catalog:browser
```

Must capture screenshots for:

```text
catalog hub
macro-object detail
table explorer validation error
table detail
reference option validation
schema guidance path inspector
```

Current baseline screenshots captured by the browser journey:

```text
output/gui-qa/catalog/01-catalog-hub.png
output/gui-qa/catalog/02-rate-record-detail.png
output/gui-qa/catalog/03-rate-record-route-detail.png
output/gui-qa/catalog/04-table-validation-error.png
output/gui-qa/catalog/05-reference-validation-error.png
output/gui-qa/catalog/06-macro-switch-recovery.png
output/gui-qa/catalog/07-table-explorer.png
output/gui-qa/catalog/08-table-detail.png
output/gui-qa/catalog/09-reference-options.png
output/gui-qa/catalog/10-reference-options-validation-error.png
output/gui-qa/catalog/11-schema-guidance.png
output/gui-qa/catalog/12-schema-guidance-paths.png
```

Layer 3 backend:

```text
python -m pytest tests/test_catalog_core.py tests/test_reference_catalog.py
```

Backend tests must prove Data Dictionary validation, macro-object load plan,
reference option policy, schema guidance safety, and no local schema/path leak.

## 8. Implementation Slices

### Slice 1: Route Skeleton

Deliver the route family and move the current macro-object detail out of the
hub:

```text
/catalog
/catalog/macro-objects/:macroObjectCode
/catalog/tables
/catalog/schema-guidance
```

Acceptance:

```text
hub is no longer overloaded
macro-object detail has Back to Catalog
existing Catalog browser QA passes after route updates
screenshots captured
```

2026-05-26 Slice 1A delivered:

```text
/catalog/macro-objects/:macroObjectCode opens with a route-level detail header.
The detail route has a visible Back to Catalog link.
Direct URL recovery loads the backend macro-object detail, tables, load plan,
Data Dictionary cross-check, and schema links for the route macro object.
Changing the effective macro object now clears stale table, column, reference,
error, and running validation state whether the change came from a click or a
route.
Browser QA captures the direct route detail screenshot.
```

2026-05-26 Slice 1B delivered:

```text
Macro-object rows on /catalog now navigate to
/catalog/macro-objects/:macroObjectCode instead of changing hidden local
selection state.
The /catalog hub no longer renders the selected macro object's table/load-plan
detail side panel; those details belong to the route-level macro-object screen.
Validation forms remain recoverable on the hub until the dedicated table and
reference routes are delivered.
Switching from a validation state to a macro-object route clears stale table,
column, reference, error, and running validation state.
Browser QA now proves hub -> row click -> detail -> Back to Catalog, direct URL
detail recovery, validation error screenshots, and macro-switch recovery.
```

### Slice 2: Table Explorer

Deliver `/catalog/tables` and `/catalog/tables/:tableName`.

Acceptance:

```text
table search and table validation are backend-owned
table detail loads columns from backend
column validation sits on table detail
invalid table and invalid column recovery are tested
```

2026-05-26 Slice 2A delivered:

```text
/catalog/tables opens a focused Catalog Table Explorer with table search
instead of adding more Data Dictionary rows to the Catalog hub.
Table rows navigate to /catalog/tables/:tableName.
/catalog/tables/:tableName opens a route-level table detail with Back to
Catalog and Back to Tables links.
The detail route loads backend-owned table definition and table columns through
GET /api/v1/catalog/tables/{table_name} and
GET /api/v1/catalog/tables/{table_name}/columns.
Browser QA captures table explorer and table detail screenshots.
```

### Slice 3: Reference Options

Deliver `/catalog/reference-options`.

Acceptance:

```text
reference options are filtered by active/backend context
reference validation shows backend policy reasons
invalid domain/value recovery is tested
```

2026-05-26 Slice 3A delivered:

```text
/catalog/reference-options opens a focused route-level reference option browser
instead of adding reference lists to the Catalog hub.
The route loads backend-owned option data from
GET /api/v1/catalog/reference/options?object_type=&domain_name= and displays
allowed domain scope from the backend payload.
The route keeps a compact reference validation form beside the option scope
controls so invalid value/domain recovery stays next to the user's lookup task.
The Catalog hub now exposes explicit Table Explorer and Reference Options
return-safe utility links.
Browser QA captures reference option list and route-level reference validation
error screenshots.
```

### Slice 4: Schema Guidance

Deliver `/catalog/schema-guidance`.

Acceptance:

```text
schema readiness, roots, service operations, and paths are inspectable
local schema file paths are not displayed
macro-object schema links navigate back to macro details
```

2026-05-26 Slice 4A delivered:

```text
/catalog/schema-guidance opens a focused route-level schema guidance inspector.
The route displays backend-owned readiness metrics, envelope roots, macro roots,
root picker actions, selected XML paths, and macro-object readiness rows.
The /catalog hub no longer renders the full schema guidance workspace; it now
offers a clear Schema Guidance utility link beside Table Explorer and Reference
Options.
Browser QA seeds a synthetic client-safe schema pack, indexes it through the
backend API, opens the route, selects a root, verifies path rows, and captures
schema guidance screenshots.
```

### Slice 5: Completion Review

Update docs, Linear, tests, screenshots, and GitHub evidence together.

Acceptance:

```text
Catalog Core completion review exists
functional QA matrix updated
module roadmap index updated
all Catalog React, browser, backend, build, and diff checks pass
```

2026-05-26 Slice 5 delivered:

```text
GUI_CATALOG_CORE_ROUTE_SEPARATION_COMPLETION_REVIEW_2026_05_26.md records the
route inventory, delivered UX decisions, backend contract alignment, QA
evidence, screenshot evidence, covered recovery paths, remaining follow-up
scope, and completion decision.
Linear OTM-90 and GitHub PR #182 were updated with the final route-separation
evidence.
```

## 9. Explicit Non-Goals

```text
manual editing of Data Dictionary tables
manual editing of macro-object canonical definitions
displaying local XML/schema/data dictionary file paths
real client reference data
schema-pack upload/indexing by normal users
module-specific workflow execution inside Catalog Core
```

Catalog Core is the source of truth and inspection surface. It should help
other modules act correctly, not become another overloaded workflow module.
