# Task Contract: Settings Setup Recovery UX

**Status:** active
**Date:** 2026-05-27

## Objective

Finish the next Settings completion slice by making setup selector empty states
and recovery paths visible. When workspace, project, environment, role, user,
grant, or policy setup cannot proceed, the Settings surface must show the
backend-owned blocker/action state and provide a clear return path to Cockpit.

## Original User Request

The user asked to continue the next step after Settings role/grant review.

## Interpreted Scope

- Add UI-level setup recovery state using existing Settings scope authority
  payloads.
- Show empty/blocked selector states for setup authoring forms.
- Add a visible `Return to Cockpit` path from Settings setup.
- Keep setup ownership in Settings and avoid adding separate Admin Console
  routes.
- Validate with frontend test, build, browser QA, and docs.

## Out Of Scope

- New backend permission semantics.
- Create/edit/detail/retire setup subroutes.
- Deleting or hiding existing modules.
- Changing the active module sequence.

## Allowed Files Or Areas

- `frontend/src/modules/admin/AdminConsoleView.tsx`
- `frontend/src/app/App.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_SETTINGS_SETUP_RECOVERY_UX.md`
- `docs/superpowers/plans/2026-05-27-settings-setup-recovery-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Backend route behavior unless a failing test proves a contract gap.
- Operational modules outside Settings.
- Figma artifacts and generated QA fixtures outside this slice.

## Acceptance Criteria

- Settings shows a setup recovery area with backend blocker/action status.
- Settings includes a visible `Return to Cockpit` link.
- Empty selectors show clear blocked state text instead of blank controls.
- Grant authoring clearly reports missing role/user/project/environment
  prerequisites.
- Access-policy authoring reports missing project prerequisites.
- Tests and browser QA cover the recovery state.

## Validation Plan

```powershell
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check
```

## Risks

- Too much helper text can make Settings feel like documentation. Keep the
  text compact and status-like.
- Do not imply the unavailable actions are frontend-only decisions; blockers
  must mirror backend-owned state.

## Challenge Notes

This slice intentionally does not create route-level setup detail screens. That
is a later, larger Settings route-family slice if approved.

## Decision

Proceed with a focused UI recovery and empty-state pass.
