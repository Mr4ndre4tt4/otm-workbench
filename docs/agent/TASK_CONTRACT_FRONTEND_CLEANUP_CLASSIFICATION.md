# Task Contract - Frontend Cleanup Classification

**Date:** 2026-05-28
**GitHub issue:** #233
**Status:** implemented and ready for PR

## Objective

Classify frontend cleanup candidates before any route/component deletion,
archive move, or source cleanup.

## Scope

- Review the active current-phase route inventory.
- Classify active, excluded/internal, special, test, and browser QA surfaces.
- Identify safe next implementation slices.
- Keep the slice documentation-only.

## Out Of Scope

- Deleting route source files.
- Archiving docs.
- Removing browser QA scripts.
- Reintroducing excluded modules into navigation.
- Integration Mapping implementation changes.

## Allowed Files

- `docs/agent/FRONTEND_CLEANUP_CANDIDATE_CLASSIFICATION.md`
- `docs/agent/TASK_CONTRACT_FRONTEND_CLEANUP_CLASSIFICATION.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Acceptance Criteria

- Cleanup candidates are classified as keep, hide, absorb, alter, archive,
  remove, or create.
- Active UI phase routes remain clearly protected.
- Excluded/internal surfaces have a treatment and validation requirement.
- The next implementation slices are reviewable and non-destructive by default.
- `git diff --check` passes.

## Decision

Proceed with a docs-only classification artifact so future cleanup can be
approved and implemented in small PRs instead of broad local edits.
