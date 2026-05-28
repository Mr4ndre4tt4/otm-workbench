# Task Contract: Order Release Same-Name Context Isolation

**Date:** 2026-05-28
**GitHub Issue:** #218

## Objective

Revalidate that Order Release templates and batches are scoped by active
project, environment, and client/domain even when templates share the same
code/name or batches share the same file name.

## Original User Request

Continue with the next roadmap step using small GitHub-versioned slices.

## Interpreted Scope

- Add focused backend regression tests for same-name Order Release templates
  across domains and environments while preserving globally unique template
  code-family semantics.
- Add focused backend regression tests for same-name Order Release batches
  across domains and environments.
- Preserve existing Order Release API behavior.
- Record validation and handoff evidence.

## Out Of Scope

- Integration Mapping work.
- Frontend redesign or browser screenshot evidence.
- Broad Order Release feature changes.
- Route cleanup or module reintroduction.

## Allowed Files Or Areas

- `tests/test_order_release_generator_foundation.py`
- `tests/test_order_release_generator_batches.py`
- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping code, tests, docs, and browser scripts.
- Unrelated dirty worktree changes.

## Acceptance Criteria

- A normal active-context user sees only the same-name private template in the
  active project, domain, and environment.
- Hidden same-name templates cannot be versioned or used for direct batch
  creation.
- A normal active-context user sees only the same-name batch in the active
  project, domain, and environment.
- Hidden same-name batches cannot be opened or previewed through direct routes.
- DBA/all-domain visibility remains constrained to the active environment.
- Tests use synthetic data only.

## Validation Plan

- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -k "same_name or active_context_scope or dba_context" -q`
- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -q`

## Risks

- The local worktree contains many unrelated changes; staging must be scoped.
- Same template names or file names can hide leaks if assertions only check
  labels, so tests must assert IDs and direct route access.

## Challenge Notes

No scope conflict found. This is a context-isolation regression slice aligned
with the current validation matrix and does not touch the reserved Integration
Mapping workstream.

## Decision

Proceed as a small GitHub-versioned validation slice for #218.
