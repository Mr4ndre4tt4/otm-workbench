# Task Contract: Excluded Component Dependency Map

**Date:** 2026-05-28
**GitHub issue:** #239
**Status:** validated

## Objective

Document dependencies for excluded, internal, absorbed, and special frontend
components before any future source removal proposal.

## In Scope

- Map Catalog Core, Evidence Hub, Admin Console, Developer Tools, Component
  Gallery, and Coordinate Quality frontend dependencies.
- Identify active dependencies such as Settings reusing `AdminConsoleView` and
  Master Data owning Coordinate Quality.
- Record removal prerequisites and safe follow-ups.
- Update cleanup classification, validation report, and handoff docs.

## Out of Scope

- Deleting source files.
- Moving components.
- Rewriting module routes.
- Browser screenshots.
- Integration Mapping implementation changes.

## Acceptance Criteria

- A governance doc maps source files, import/render paths, current treatment,
  and removal status for excluded/internal components.
- Active dependencies are explicitly called out before any future deletion work.
- Validation confirms direct route guard and backend navigation coverage remain
  green.

## Validation Plan

- `npm test -- src/app/routes/WorkbenchRoute.test.tsx`
- `python -m pytest tests/test_modules_navigation.py -q`
- `git diff --check`

## Risks

- This map is a point-in-time inventory; future implementation slices should
  rerun import searches before deleting or moving source.
