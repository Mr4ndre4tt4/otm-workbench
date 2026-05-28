# Task Contract: Master Data Same-Name Context Isolation

**Date:** 2026-05-28
**GitHub Issue:** #217

## Objective

Revalidate that Master Data workbook batch visibility is scoped by active
project, environment, and client/domain even when batches share the same file
name.

## Original User Request

Continue with the next roadmap step using small GitHub-versioned slices.

## Interpreted Scope

- Add focused backend regression tests for same-name Master Data batches across
  domains and environments.
- Preserve existing Master Data API behavior.
- Record validation and handoff evidence.

## Out Of Scope

- Integration Mapping work.
- Frontend redesign or browser screenshot evidence.
- Broad Master Data feature changes.
- Route cleanup or module reintroduction.

## Allowed Files Or Areas

- `tests/test_master_data_templates.py`
- `docs/agent/TASK_CONTRACT_MASTER_DATA_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping code, tests, docs, and browser scripts.
- Unrelated dirty worktree changes.

## Acceptance Criteria

- A normal active-context user sees only the same-name batch in the active
  project, domain, and environment.
- Direct detail/output/csv route access to same-name batches in another domain
  or environment returns `404`.
- DBA/all-domain visibility remains constrained to the active environment.
- Tests use synthetic data only.

## Validation Plan

- `python -m pytest tests/test_master_data_templates.py -k "same_name or active_context_scope or dba_context" -q`
- `python -m pytest tests/test_master_data_templates.py -k "context_scope or dba_context or same_name or require_active_context" -q`

## Risks

- The local worktree contains many unrelated changes; staging must be scoped.
- Same display file names can hide leaks if assertions only check labels, so
  tests must assert batch IDs and route access.

## Challenge Notes

No scope conflict found. This is a context-isolation regression slice aligned
with the current validation matrix and does not touch the reserved Integration
Mapping workstream.

## Decision

Proceed as a small GitHub-versioned validation slice for #217.
