# Integration Mapping Studio Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Integration Mapping Studio should help users define, validate, preview, and
document integrations between source and target payloads using backend-owned
schemas, mappings, rules, previews, specs, artifacts, and evidence.

## 2. Current Evidence

The consolidated spec defines a route-level accelerator: definition hub, create
definition, definition cockpit, systems/endpoints, payloads/schemas, mapping
workspace, rule detail, rules, review, preview, spec, artifacts, and systems
library.

## 3. Validated Target Scope

Integration Mapping Studio should be organized around a versioned integration
definition:

- definition library and search;
- create/edit/copy/retire definition routes;
- systems and endpoints;
- source/target schemas and schema roots;
- mapping workspace with backend-owned suggestions;
- rule detail and grouped rule families;
- review, preview, spec, artifacts, and evidence.

## 4. Explicit Non-Scope

- Do not present raw JSON editing as the primary mapping experience.
- Do not use frontend-only mapping suggestions as durable truth.
- Do not hide alias/path blockers.
- Do not execute real external integrations without governed connection,
  credential, environment, and audit controls.

## 5. Cleanup Watchlist

- One overloaded staged workspace.
- Suggestions generated only in frontend.
- Mapping errors that do not identify alias/path/scope.
- Preview/spec actions available before blockers are resolved.

## 6. Backend Contract Dependencies

- definition list/detail/create/update;
- systems/endpoints;
- source and target schema documents;
- schema root/path contracts from Catalog Core;
- mapping rules, joins, lookups, loops, response handlers;
- backend-owned suggestions and scoring;
- validation, preview, spec generation, artifacts, and evidence.

## 7. Wireframe Inputs

Required route frames:

- definition hub;
- new definition;
- definition cockpit;
- systems/endpoints;
- payloads/schemas;
- mapping workspace;
- rule detail/edit;
- rules grouped review;
- final review;
- preview;
- generated spec;
- artifacts;
- systems library.

Required states:

- no definitions;
- schema root missing;
- required target fields missing;
- invalid alias/path;
- backend suggestions unavailable;
- preview blocked;
- preview artifact generated;
- stale schema reference.

## 8. Open Decisions

- Which rule families must be first-class routes versus sections.
- How much NDD-like scenario guidance should appear before generic mapping
  patterns.
- How to display provenance for multi-hop joins without overloading the user.

## 9. Acceptance For Wireframe Phase

Integration Mapping can move to Penpot when the definition-centered model and
route-level mapping/review/preview/spec flow are accepted.
