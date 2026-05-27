# Task Contract: Settings Policy Binding UX

**Status:** active
**Date:** 2026-05-27

## Objective

Finish the next Settings slice by making access-policy authoring and binding
review understandable from the Settings surface. The UI must show which
project, visibility, and client/domain a policy can bind to, using
backend-owned metadata instead of requiring users to infer it from raw JSON.

## In Scope

- Revalidate Settings against the current UI phase rules and the Configuration
  Settings deep-flow baseline.
- Add backend-owned access-policy binding guidance to the Settings access model.
- Show a Settings policy-binding review surface with project, visibility,
  domain, active-context match, and binding requirements.
- Preserve project/client-domain/environment access segregation.
- Add focused backend and frontend tests for the new contract and UI.
- Update handoff/validation evidence when the slice is validated.

## Out Of Scope

- Secret storage or credential reveal.
- A full policy engine beyond the current access-policy metadata contract.
- Moving setup ownership out of Settings.
- Reintroducing separate Admin Console, Jobs dashboard, Developer Tools, or
  Evidence Hub as top-level UI modules.
- Broad frontend route cleanup or deletion.

## Files Allowed

- `src/otm_workbench/platform/routes.py`
- `tests/test_operational_context.py`
- `frontend/src/platform/types/platform.ts`
- `frontend/src/modules/admin/AdminConsoleView.tsx`
- `frontend/src/app/App.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_SETTINGS_POLICY_BINDING_UX.md`
- `docs/superpowers/plans/2026-05-27-settings-policy-binding-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Acceptance Criteria

- Access policies returned by `/api/v1/platform/settings/access-model` include
  binding guidance for project, visibility, and domain.
- Scoped setup users only see policy guidance for their allowed active project.
- Settings renders a clear policy-binding review with active-context status.
- Rule JSON remains metadata only and is not treated as a secret or credential
  surface.
- Backend and frontend tests cover the new contract.
- Browser QA evidence is captured before the slice is handed off.

## Risks And Guardrails

- Do not make access policies look like live authorization execution when this
  slice is only binding guidance.
- Do not leak cross-project policy metadata to scoped users.
- Keep labels, disabled reasons, and binding rules backend-owned.
