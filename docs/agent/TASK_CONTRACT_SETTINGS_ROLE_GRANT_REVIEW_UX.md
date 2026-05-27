# Task Contract: Settings Role And Grant Review UX

**Status:** active
**Date:** 2026-05-27

## Objective

Continue Settings completion by making role/grant setup reviewable in the UI.
Users must be able to see which user receives which role, the project,
environment, and client/domain scope for the grant, and whether that grant
matches the active context.

## Original User Request

The user asked to continue the next step in the To-Be adaptation sequence after
Settings policy-binding UX.

## Interpreted Scope

- Add backend-owned grant binding guidance to the Settings access model.
- Keep role and grant authoring inside Settings.
- Render a grant-binding review section with user, role, project, environment,
  domain, and active-context status.
- Preserve the current access controls for DBA and scoped setup users.
- Add backend/frontend tests and QA evidence.

## Out Of Scope

- Building a full role-management workflow with edit/delete/retire.
- Moving Settings to a renamed component or new route family.
- New permission semantics beyond the existing role/capability/grant model.
- Reintroducing separate Admin Console, Jobs dashboard, or generic dashboards.

## Allowed Files Or Areas

- `src/otm_workbench/platform/routes.py`
- `tests/test_operational_context.py`
- `frontend/src/platform/types/platform.ts`
- `frontend/src/modules/admin/AdminConsoleView.tsx`
- `frontend/src/app/App.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_SETTINGS_ROLE_GRANT_REVIEW_UX.md`
- `docs/superpowers/plans/2026-05-27-settings-role-grant-review-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Unrelated module runtime behavior.
- Navigation cleanup/deletion.
- Data Dictionary, Oracle docs, and fixture generation outside this slice.

## Acceptance Criteria

- Settings access-model grants include backend-owned binding labels,
  requirements, and active-context match state.
- Scoped users still only receive grants visible to their active project or to
  themselves when they lack grant management authority.
- Settings shows a grant-binding review with clear status and scope details.
- Tests cover backend contract and frontend rendering.
- Browser QA evidence is captured.

## Validation Plan

```powershell
pytest tests/test_operational_context.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check
```

## Risks

- Grant review can imply editable authorization if it is styled like an action
  table. Keep it review-focused.
- Cross-project grants must not leak to scoped users.
- Existing dirty worktree changes must remain untouched.

## Challenge Notes

This is a Settings completion slice, not a full access-control redesign.

## Decision

Proceed with a focused backend contract and UI review panel.
