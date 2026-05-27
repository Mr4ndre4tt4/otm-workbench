# Order Release Generator Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Order Release Generator should create governed OTM order release XML artifacts
from versioned templates and operator-entered rows, with schema guidance,
preview, artifact generation, and guarded submit readiness.

## 2. Current Evidence

The consolidated spec defines a route-level generator workflow: generator hub,
template creation/detail/versioning, batch creation/detail, row editor, XML
preview, artifacts, and submit readiness.

## 3. Validated Target Scope

Order Release Generator should be organized around templates and batches:

- template library/search;
- template create/detail/versioning;
- batch creation from template;
- batch detail and row editor;
- XML preview with summary/provenance;
- artifact generation/download;
- guarded OTM submit readiness.

## 4. Explicit Non-Scope

- Do not use raw JSON as the primary data entry model.
- Do not treat raw XML preview as sufficient user feedback.
- Do not enable real submit-to-OTM without governed connection, credential,
  capability, audit, and retry/job controls.
- Do not expose real client order data.

## 5. Cleanup Watchlist

- Raw JSON row editing.
- Raw XML as the only preview.
- Submit readiness that is frontend-inferred.
- Template switching that leaves stale row or preview state.

## 6. Backend Contract Dependencies

- template list/create/detail/version;
- schema root links for Transmission and Release;
- batch create/detail;
- row validation and editor defaults;
- XML preview and validation summary;
- artifact generation/download;
- submit readiness blockers.

## 7. Wireframe Inputs

Required route frames:

- generator hub;
- create template;
- template detail;
- template versioning;
- create batch;
- batch detail;
- row editor;
- XML preview;
- artifacts;
- submit readiness.

Required states:

- no templates;
- invalid template schema root;
- no batch rows;
- row validation blockers;
- preview blocked;
- XML preview ready;
- artifact generated;
- submit blocked by missing connection/credentials/capability.

## 8. Open Decisions

- Whether first generator path targets Transmission-wrapped Release only.
- Which row fields are required for the first operational template.
- How much Catalog schema-path guidance should be shown in template authoring.

## 9. Acceptance For Wireframe Phase

The module can move to Penpot when template-guided batch generation and guarded
submit readiness are accepted as the organizing model.
