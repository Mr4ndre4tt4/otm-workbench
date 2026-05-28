# Task Contract - Cockpit Context Selector Evidence

**Date:** 2026-05-28
**GitHub issue:** #215
**Status:** in progress

## Objective

Capture Cockpit context selector and route recovery evidence before the next
Cockpit/Rates delivery lane.

## Original User Request

Continue with the next roadmap step after the context-isolation validation
matrix.

## Interpreted Scope

- Revalidate Project Cockpit backend summary contracts for Public View and
  private active context.
- Revalidate frontend Cockpit v3 macro groups.
- Strengthen browser shell QA with navigation freshness checks and screenshot
  evidence for Cockpit context selector route recovery.
- Preserve current UI phase navigation and avoid excluded top-level modules.

## Out Of Scope

- Cockpit redesign implementation.
- New Cockpit features.
- Settings setup changes.
- Rates implementation.
- Integration Mapping changes.

## Allowed Files Or Areas

- `frontend/scripts/functional-shell-browser.mjs`
- `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping implementation files.
- Unrelated dirty workspace changes.

## Acceptance Criteria

- Backend Project Cockpit summary tests pass.
- Frontend Cockpit v3 test passes.
- Browser shell QA verifies live navigation IDs before screenshot capture.
- Screenshot evidence shows the current UI phase sidebar, Cockpit context
  selector, and no excluded top-level modules.
- Validation and handoff docs are updated.

## Validation Plan

- `python -m pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q`
- `npm test -- src/app/App.test.tsx -t "Cockpit"`
- `npm run qa:functional:shell:browser`

## Risks

- Browser QA requires a fresh backend/frontend runtime and synthetic QA user.
- The local workspace has unrelated dirty files; commit only this slice.

## Challenge Notes

This slice is evidence and QA hardening, not a broad Cockpit redesign.

## Decision

Proceed with focused test execution and browser QA script hardening.
