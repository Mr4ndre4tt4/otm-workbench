# Developer Tools Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Developer Tools should provide controlled technical diagnostics for DBA, MASTER,
and developer users without contaminating the consultant experience.

## 2. Current Evidence

The active redesign spec defines a guarded diagnostics hub with Data Dictionary,
FK Catalog, Schema Pack Diagnostics, Environment Readiness, and future
diagnostic-run detail.

## 3. Validated Target Scope

Developer Tools should be treated as a restricted diagnostics route family:

- technical diagnostics hub;
- Data Dictionary explorer and table detail;
- FK Catalog explorer;
- schema pack diagnostics;
- environment readiness;
- diagnostic run detail and trace actions as future explicit scope.

## 4. Explicit Non-Scope

- Do not expose Developer Tools to normal users.
- Do not expose local file paths, credentials, endpoints, or raw payloads.
- Do not become a parallel Catalog Core for normal product users.
- Do not allow destructive technical actions without governed route/modals.

## 5. Cleanup Watchlist

- Public technical tools.
- Local path leakage.
- Generic placeholders.
- Diagnostics that expose unsafe payloads or credentials.
- Duplicate Catalog functionality without role distinction.

## 6. Backend Contract Dependencies

- platform dev-tools summary;
- feature flags/capabilities;
- Data Dictionary list/detail;
- FK Catalog relationships;
- schema-pack/root metadata;
- environment readiness checks;
- disabled reasons and guarded actions.

## 7. Wireframe Inputs

Required route frames:

- technical diagnostics hub;
- Data Dictionary explorer;
- Data Dictionary table detail;
- FK Catalog;
- schema pack diagnostics;
- environment readiness;
- diagnostic run detail placeholder/future route.

Required states:

- unauthorized user;
- feature disabled;
- active context missing;
- Data Dictionary unavailable;
- no FK relationships;
- schema pack failed;
- environment check blocked;
- diagnostic run failed.

## 8. Open Decisions

- Which diagnostics belong in Developer Tools versus Admin.
- Whether schema-pack import/indexing is Admin-only, Developer Tools-only, or
  split by capability.
- Which diagnostic actions can be safe read-only MVP actions.

## 9. Acceptance For Wireframe Phase

Developer Tools can move to Penpot when it remains clearly restricted,
diagnostic, read-mostly, and separated from normal module workflows.
