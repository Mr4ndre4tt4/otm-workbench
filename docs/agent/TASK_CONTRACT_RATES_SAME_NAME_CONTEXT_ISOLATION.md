# Task Contract: Rates Same-Name Context Isolation

**Date:** 2026-05-28
**GitHub Issue:** #216

## Objective

Revalidate that Rates batch visibility is scoped by active project,
environment, and client/domain even when batches share the same display name.

## Original User Request

Continue with the next roadmap step while keeping GitHub visibility and small
delivery slices.

## Interpreted Scope

- Add a focused backend regression test for same-name Rates batches across
  domains and environments.
- Preserve existing Rates API behavior.
- Record validation and handoff evidence.

## Out Of Scope

- Integration Mapping work.
- Frontend redesign or browser screenshot evidence.
- Broad Rates feature expansion such as advanced search, row mutation, or
  approval UX changes.
- Route cleanup or module reintroduction.

## Allowed Files Or Areas

- `tests/test_rates_batches.py`
- `docs/agent/TASK_CONTRACT_RATES_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping code, tests, docs, and browser scripts.
- Unrelated dirty worktree changes.

## Acceptance Criteria

- A normal active-context user sees only the same-name batch in the active
  domain and environment.
- Direct detail access to same-name batches in another domain or environment
  returns `404`.
- DBA/all-domain visibility remains constrained to the active environment.
- Tests use synthetic data only.

## Validation Plan

- `python -m pytest tests/test_rates_batches.py -k "same_name or active_context_scope or dba_context" -q`
- `python -m pytest tests/test_rates_batches.py tests/test_rates_summary.py -q`

## Risks

- The local worktree contains many unrelated changes; staging must be scoped.
- Same display names can hide leaks if assertions only check labels, so tests
  must assert IDs and route access.

## Challenge Notes

No scope conflict found. This is a context-isolation regression slice aligned
with the current matrix and does not touch the reserved Integration Mapping
workstream.

## Decision

Proceed as a small GitHub-versioned validation slice for #216.
