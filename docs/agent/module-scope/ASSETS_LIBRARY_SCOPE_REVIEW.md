# Assets Library Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Assets Library should manage project assets, versions, metadata,
classifications, links, downloads, and archive state. It should support
collaboration and traceability without becoming a generic file manager.

## 2. Current Evidence

The consolidated spec defines assets hub, library, create/edit metadata, asset
detail, versions, version upload, links, classifications, and archive routes.

## 3. Validated Target Scope

Assets Library should be treated as a controlled asset lifecycle module:

- asset discovery and filtered library;
- create and edit metadata;
- version upload and download;
- guided links to modules, macro objects, OTM tables, evidence, and artifacts;
- custom classifications with system-protected guards;
- archive with impact/restriction visibility.

## 4. Explicit Non-Scope

- Do not become a generic folder explorer.
- Do not allow unvalidated links to module objects or OTM metadata.
- Do not mutate archived assets.
- Do not expose unsafe artifacts or local paths.

## 5. Cleanup Watchlist

- Stacked create/upload/link/list panels.
- Classification authoring mixed into asset creation.
- Ungoverned target pickers.
- Archived asset mutation controls.

## 6. Backend Contract Dependencies

- asset list/detail/search;
- create/update metadata validation;
- version upload/download;
- guided target lookup;
- evidence/artifact link validation;
- classification create/update guards;
- archive lifecycle and available actions.

## 7. Wireframe Inputs

Required route frames:

- Assets hub;
- asset library;
- new asset;
- asset detail;
- edit metadata;
- versions;
- upload version;
- links;
- classifications;
- new classification;
- edit classification;
- archive asset.

Required states:

- no assets;
- invalid metadata classification;
- upload blocked;
- selected file pending;
- invalid link target;
- evidence/artifact target unavailable;
- archived asset;
- system classification protected.

## 8. Open Decisions

- Which asset classifications are product-level defaults.
- Whether schema packs live in Assets Library, Admin, Developer Tools, or all
  three through different surfaces.
- Which link types are mandatory for the first redesign pass.

## 9. Acceptance For Wireframe Phase

Assets can move to Penpot when asset lifecycle, versioning, and governed links
are accepted as the core model.
