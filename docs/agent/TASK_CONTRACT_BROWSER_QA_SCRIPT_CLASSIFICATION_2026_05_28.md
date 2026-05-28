# Task Contract: Browser QA Script Classification

**Date:** 2026-05-28
**GitHub issue:** #237
**Status:** validated

## Objective

Classify browser QA scripts so future screenshot evidence follows the current
backend-owned navigation scope and does not validate excluded top-level routes.

## In Scope

- Inventory browser QA scripts under `frontend/scripts/`.
- Mark scripts as active, reserved, internal, deferred, or stale.
- Document current screenshot rules and safe follow-ups.
- Update validation and handoff docs.

## Out of Scope

- Deleting scripts.
- Capturing new screenshots.
- Rewriting browser journeys.
- Integration Mapping implementation work.

## Acceptance Criteria

- A governance doc names each browser QA script and its current evidence rule.
- Scripts targeting `/admin`, Coordinate Quality top-level, or other excluded
  surfaces are marked as not valid current acceptance evidence.
- Validation confirms the script files still parse.

## Validation Plan

- `Get-ChildItem frontend/scripts -Filter *.mjs | ForEach-Object { node --check $_.FullName }`
- `git diff --check`

## Risks

- Some internal scripts still remain callable through `package.json`; this slice
  classifies evidence validity before any command removal or journey rewrite.
