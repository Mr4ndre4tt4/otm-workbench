# Rates Studio Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Rates Studio should help implementation teams prepare, validate, approve, and
export tariff/rate data with client-safe evidence. It must preserve OTM table
validation through the Data Dictionary and use schema roots only as XML or
contract companions where appropriate.

## 2. Current Evidence

The consolidated spec defines a route-level Rates experience with hub, batch
library, batch creation, batch detail, staging, table detail, issues, CSV
preview, export, approval, artifacts, evidence, and Load Plan handoff.

## 3. Validated Target Scope

Rates Studio should be treated as a batch-lifecycle module:

- discover and create rate batches;
- validate table and row content;
- inspect staged tables and issues;
- build CSV previews and exports;
- approve when capability and readiness allow;
- review artifacts and evidence;
- hand off exported packages to Load Plan.

## 4. Explicit Non-Scope

- Do not promise real OTM sandbox execution without proof.
- Do not derive CSV load order from XSD.
- Do not execute approval inline from a list row.
- Do not show all lifecycle panels on one screen.

## 5. Cleanup Watchlist

- Single-page stacked Rates panels.
- Unbounded recent batch lists.
- Approval controls without review summary.
- Frontend-owned validation or action availability.

## 6. Backend Contract Dependencies

- rate batch list/search/detail;
- batch creation and staged table payloads;
- Data Dictionary validation;
- issue summaries and blockers;
- CSV preview/export/artifact contracts;
- approval readiness and capability checks;
- evidence and Load Plan handoff metadata.

## 7. Wireframe Inputs

Required route frames:

- Rates hub;
- batch library;
- new batch;
- batch detail;
- staging workspace;
- table detail;
- issues;
- CSV preview;
- export;
- approval;
- artifacts;
- evidence;
- Load Plan handoff.

Required states:

- no batches;
- invalid table/column;
- validation blockers;
- approval blocked;
- export ready;
- export complete;
- artifact download blocked by permission.

## 8. Open Decisions

- Whether tariff template authoring belongs in Rates Studio MVP or a later
  governed authoring route.
- Which XML/schema roots should be shown as companion guidance before full
  functional validation is complete.
- How approval history should appear in evidence versus batch detail.

## 9. Acceptance For Wireframe Phase

Rates can move to Penpot when the user accepts batch lifecycle as the organizing
principle and approval/export as route-level critical operations.
