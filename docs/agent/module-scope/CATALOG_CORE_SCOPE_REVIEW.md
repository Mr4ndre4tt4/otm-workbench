# Catalog Core Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_CATALOG_CORE_ROADMAP_SPEC.md`
**Evidence:** `docs/otm-workbench/gui/GUI_CATALOG_CORE_ROUTE_SEPARATION_COMPLETION_REVIEW_2026_05_26.md`

## 1. Original Intent

Catalog Core exists to provide shared OTM technical truth for the Workbench:

- macro-object definitions;
- Data Dictionary table and column validation;
- reference option policy;
- foreign-key and load-sequence guidance;
- schema-pack/root/path guidance for XML and integration work;
- safe, client-free contract metadata for other modules.

It is infrastructure and an inspection surface. It should help other modules
make correct OTM decisions, not become another operational workflow module.

## 2. Current Evidence

The route-separation spec and completion review show that Catalog Core has
already moved from a dense all-in-one inspector into focused routes:

```text
/catalog
/catalog/macro-objects/:macroObjectCode
/catalog/tables
/catalog/tables/:tableName
/catalog/reference-options
/catalog/schema-guidance
```

The schema-pack contract spec records shared backend support for WSDL/XSD
schema packs, schema roots, paths, service operations, macro-object schema
links, and safe evidence. The functional validation matrix records the current
guardrail that schema paths are guidance, while Data Dictionary remains the
source of truth for CSVUtil tables, columns, dependencies, and load order.

## 3. Validated Target Scope

For Penpot and future implementation planning, Catalog Core should remain a
read-only, route-level catalog explorer:

1. **Catalog Hub**
   Macro-object discovery, compact validation entry, and utility links.

2. **Macro-Object Detail**
   One macro object, its tables, dependencies, Data Dictionary cross-check,
   schema links, and module usage affordances.

3. **Table Explorer / Table Detail**
   Data Dictionary table search, table validation, column inspection, and
   column validation.

4. **Reference Options**
   Backend-owned reference option browsing and validation in active context.

5. **Schema Guidance**
   Schema-pack readiness, role-separated roots, path inspection, service
   operation summaries, and macro-object schema guidance readiness.

## 4. Explicit Non-Scope

- No manual editing of Data Dictionary tables.
- No manual editing of canonical macro-object definitions.
- No normal-user schema-pack import/indexing UI.
- No local schema, Data Dictionary, or filesystem paths in UI.
- No real client reference data.
- No module-specific workflow execution inside Catalog Core.
- No treating schema paths as CSV/load-order truth.

## 5. Cleanup Watchlist

Future cleanup planning should look for:

- duplicate Data Dictionary or FK explorers outside Catalog Core and guarded
  Developer Tools;
- schema guidance panels that expose local paths or raw schema content;
- macro-object detail content still rendered on the hub;
- validation forms that show errors away from the input that caused them;
- frontend-owned macro-object labels, aliases, readiness, or confidence.

No cleanup is approved by this review.

## 6. Backend Contract Dependencies

Wireframes should assume backend ownership for:

- macro-object list/detail/table/load-plan/cross-check/schema-link payloads;
- Data Dictionary table search, table detail, and columns;
- table, column, and reference validation responses;
- reference option scope and domain visibility;
- schema-pack readiness, roots, paths, operations, aliases, and guidance roles;
- guidance readiness and functional confidence.

## 7. Wireframe Inputs

Required route frames:

- Catalog hub;
- macro-object detail;
- table explorer;
- table detail;
- reference options browser;
- schema guidance inspector.

Required state frames:

- empty macro-object list;
- macro object with blocked schema links;
- unknown table validation;
- blocked table usage validation;
- table with many columns;
- unknown column validation;
- reference value not found;
- reference value outside active domain;
- no schema packs indexed;
- schema guidance root selected;
- path search no results;
- admin-only schema indexing unavailable to normal user.

## 8. Open Decisions

- Whether Catalog Core should expose cross-module "use this in..." links in
  the first Penpot pass or keep them as later action affordances.
- Whether schema-pack administration belongs in Admin Console or Developer
  Tools for MVP.
- Which macro objects need Data Dictionary cross-check evidence before their
  schema links become user-facing recommendations.
- How much path detail is useful before Catalog becomes too technical for a
  normal implementation lead.

## 9. Acceptance For Wireframe Phase

Catalog Core can move to Figma wireframing when:

- the user accepts this target scope;
- the wireframe brief is reviewed;
- the Penpot page keeps the hub compact and moves deep inspection into routes;
- schema guidance remains clearly marked as contract guidance, not CSV truth.
