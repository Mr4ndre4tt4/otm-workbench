# Task Contract: Integration Mapping Focus Gate

**Date:** 2026-05-28
**GitHub issue:** #241
**Status:** validated

## Objective

Prevent further drift away from the original Integration Mapping mock/spec
objective. Future "next step" work in this workstream must move the
Integration Mapping To-Be UI forward or define a direct backend/API contract
required for that UI.

## Original User Request

The user called out that progress was too slow and lost focus from the initial
mock-based Integration Mapping direction, then explicitly asked Solon to ensure
this does not happen again.

## Interpreted Scope

- Record the focus correction as a priority and delivery-pipeline rule.
- Add a decision-log entry and risk-register mitigation for focus drift.
- Update handoff so future chats resume with the corrected next step.

## Out Of Scope

- Runtime UI changes.
- Backend/API implementation.
- More generic cleanup, classification, or archive planning.
- Integration Mapping code changes in this governance-only correction slice.

## Allowed Files Or Areas

- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- Source code and migrations.
- Generated outputs and `OTM_RESOURCES/`.
- Any unrelated dirty workspace state outside this clean worktree.

## Acceptance Criteria

- The docs clearly state that the next Integration Mapping work must implement
  mock/spec-visible progress or a direct enabling API contract.
- Generic cleanup/governance slices are explicitly blocked unless they are an
  unavoidable prerequisite for the Integration Mapping mock/spec outcome.
- Future agents have a challenge rule for proposed work that does not advance
  the Integration Mapping To-Be result.

## Validation Plan

- `git diff --check`

## Risks

- This correction does not itself implement the UI; it only prevents the next
  slice from drifting again.

## Challenge Notes

The user correction is valid. The prior governance slices were safe but did not
deliver visible mock/spec progress, so continuing that pattern would be a
delivery failure for this workstream.

## Decision

Apply the focus gate immediately, then make the next implementation slice an
Integration Mapping mock/spec UI or direct enabling API slice.
