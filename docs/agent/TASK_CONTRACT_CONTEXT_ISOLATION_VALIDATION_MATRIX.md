# Task Contract - Context Isolation Validation Matrix

**Date:** 2026-05-28
**GitHub issue:** #214
**Status:** in progress

## Objective

Open the context-isolation foundation lane before continuing module
development outside Assets.

## Original User Request

Continue with the next roadmap step after closing the immediate Assets backlog.

## Interpreted Scope

- Inventory current backend coverage for active context, client/domain,
  environment, Public View, access-policy visibility, and DBA override.
- Create a module-facing validation matrix for the current UI phase.
- Run the existing operational context tests to establish a baseline.
- Identify actionable follow-up gaps for small future issues.

## Out Of Scope

- Broad frontend cleanup.
- Cockpit redesign implementation.
- New Settings UI screens.
- Integration Mapping changes.
- Route deletion or archive moves.

## Allowed Files Or Areas

- `docs/agent/`
- GitHub Issues/PR comments.

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping implementation files.
- Unrelated dirty workspace changes.

## Acceptance Criteria

- Context-isolation validation matrix exists in repo docs.
- Existing baseline validation command is recorded and passes or gaps are
  documented.
- Matrix identifies which modules already have scoped tests and which require
  follow-up implementation issues.
- GitHub issue #214 is updated with status and validation evidence.

## Validation Plan

- `python -m pytest tests/test_operational_context.py -q`
- `python -m pytest tests/test_modules_navigation.py -q`

## Risks

- The workspace contains unrelated parallel work. Commit only this governance
  slice and do not stage dirty implementation files.
- Some modules may already have partial context tests in module-specific suites;
  this pass should not claim completion unless the coverage is explicit.

## Challenge Notes

This is a foundation validation slice, not a reason to implement a large
cross-module refactor in one commit.

## Decision

Proceed with documentation, baseline validation, and follow-up issue creation
only for concrete gaps.
