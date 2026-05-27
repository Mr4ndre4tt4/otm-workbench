# Task Contract: Settings Final Revalidation

**Status:** active
**Date:** 2026-05-27

## Objective

Revalidate Settings against the current Configuration Settings deep-flow
baseline and decide whether the module can hand off to the next module slice.

## Original User Request

The user asked to continue the next step after Settings setup recovery.

## Interpreted Scope

- Compare current Settings runtime behavior with the active current UI phase,
  Figma deep-flow report, module scope notes, and recent validation evidence.
- Distinguish current-phase Settings scope from the older, broader Admin
  Console / Jobs specification.
- Record accepted coverage, non-blocking gaps, blocking gaps if any, QA
  evidence, and the next module recommendation.

## Out Of Scope

- New product implementation.
- Route deletion or Admin Console route-family creation.
- GitHub delivery updates.
- Figma edits.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_SETTINGS_FINAL_REVALIDATION.md`
- `docs/agent/module-revalidation/SETTINGS_FINAL_REVALIDATION_2026_05_27.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Source code and tests, unless verification reveals a blocking regression.
- Module specs outside Settings/Rates transition notes.

## Acceptance Criteria

- Settings final status is explicit.
- Evidence links are listed.
- Current-phase scope boundaries are clear.
- Follow-ups are separated into blocking and non-blocking.
- Next recommended module is explicit.

## Validation Plan

```powershell
npm test -- src/app/App.test.tsx -t "Settings"
pytest tests/test_operational_context.py -q
npm run build
git diff --check
```

## Risks

- The older Admin Console spec is broader than current-phase Settings. Do not
  treat out-of-phase Admin/Jogs requirements as blockers.
- Do not hide the scoped-read `403` follow-up discovered during browser QA.

## Challenge Notes

This is a governance checkpoint, not a product feature slice.

## Decision

Proceed with final Settings revalidation documentation and fresh verification.
