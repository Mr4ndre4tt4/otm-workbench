# Load Plan / Cutover Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Load Plan / Cutover should consume packages produced by Data Factory and Rates,
then manage CSVUTIL, ZIP analysis, setup review, sequence, readiness, exports,
go/no-go, and handoff evidence.

Cutover is a governed flow inside Load Plan, not a separate top-level module.

## 2. Current Evidence

The consolidated spec defines route-level package library, package detail,
checklist, readiness, CSVUTIL, ZIP review, sequence, exports, go/no-go, and
handoff screens.

## 3. Validated Target Scope

Load Plan / Cutover should be organized around a package/checklist lifecycle:

- package library and package detail;
- checklist and review queue;
- readiness generation and blockers;
- CSVUTIL build and ZIP analysis;
- load sequence;
- readiness/export packages;
- go/no-go;
- guarded cutover handoff.

## 4. Explicit Non-Scope

- Do not split Cutover into a separate public module.
- Do not run real OTM/CSVUTIL execution unless explicitly governed later.
- Do not place every cutover surface on the hub.
- Do not allow handoff commit without backend eligibility.

## 5. Cleanup Watchlist

- Long stacked Load Plan pages.
- Cutover presented as a dashboard decoration.
- Stale package state after switching packages.
- Handoff actions without review summary.

## 6. Backend Contract Dependencies

- package list/detail/search;
- checklist create/update/readiness;
- ZIP analysis and setup review decisions;
- sequence snapshots;
- readiness exports;
- CSVUTIL artifacts;
- go/no-go and handoff eligibility;
- evidence and guarded downloads.

## 7. Wireframe Inputs

Required route frames:

- Load Plan hub;
- package library;
- package detail;
- checklist;
- readiness;
- CSVUTIL;
- ZIP review;
- sequence;
- exports;
- go/no-go;
- handoff.

Required states:

- no packages;
- package blocked by missing export evidence;
- checklist incomplete;
- readiness blocked;
- CSVUTIL artifact ready;
- ZIP review uncertain items;
- handoff ineligible;
- handoff committed.

## 8. Open Decisions

- Whether review queue should be its own route or embedded in package detail.
- How much CSVUTIL technical detail is useful to functional users.
- What evidence must be mandatory before handoff eligibility.

## 9. Acceptance For Wireframe Phase

The module can move to Penpot when package/checklist lifecycle is accepted as
the organizing model and handoff remains a route-level governed operation.
