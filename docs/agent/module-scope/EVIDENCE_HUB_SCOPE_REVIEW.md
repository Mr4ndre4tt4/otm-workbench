# Evidence Hub Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Evidence Hub is the canonical client-safe evidence and artifact audit surface.
It lets users inspect what was produced, where it came from, what it proves,
and whether downloads or archive packages are allowed.

## 2. Current Evidence

The consolidated spec defines evidence hub, evidence detail, guarded download
review, archive builder, archive detail/library, source object timeline,
artifact detail, and optional audit search.

## 3. Validated Target Scope

Evidence Hub should be treated as a traceability and handoff module:

- filter and inspect evidence;
- review source object and module lineage;
- guard artifact downloads through backend hash/audit;
- build archive packages from client-safe evidence;
- inspect archive history;
- review artifacts without exposing local paths or raw payloads.

## 4. Explicit Non-Scope

- Do not expose raw payloads or raw manifests as primary UI.
- Do not expose local filesystem paths.
- Do not rebuild source module logic inside Evidence Hub.
- Do not bypass permission, hash, sensitivity, or audit checks for downloads.

## 5. Cleanup Watchlist

- Evidence views that act like generic file browsers.
- Raw technical payload blocks.
- Archive actions without eligibility/review.
- Artifact links that reveal local paths.

## 6. Backend Contract Dependencies

- evidence list/detail/search;
- artifact metadata and guarded download readiness;
- archive package create/list/detail;
- source object timeline;
- audit metadata;
- sensitivity and capability enforcement.

## 7. Wireframe Inputs

Required route frames:

- Evidence hub;
- evidence detail;
- guarded download review;
- archive builder;
- archive library;
- archive detail;
- source object timeline;
- artifact detail;
- optional audit search.

Required states:

- no evidence;
- filter returns no results;
- evidence without artifact;
- download blocked;
- hash verification failed;
- archive ineligible;
- archive ready;
- artifact sensitive.

## 8. Open Decisions

- Whether audit search is needed in the first redesign pass.
- How much source module context should be shown before linking back.
- Which archive templates should be backend-owned in MVP.

## 9. Acceptance For Wireframe Phase

Evidence Hub can move to Penpot when it is accepted as the traceability and
handoff surface, not a raw file explorer.
