# Settings Final Revalidation

**Status:** accepted for current UI phase with non-blocking follow-ups
**Date:** 2026-05-27
**Active Figma baseline:** `15 / Configuration Settings Deep Flow`

## Scope Decision

Settings is accepted as the current UI phase setup surface for:

- project setup;
- client/domain and environment setup;
- profiles;
- users;
- roles and capabilities;
- grants;
- access policies;
- backend-owned blocker/action visibility.

The older `GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md` describes a larger Admin
Console with jobs, audit, feature flags, OTM connections, and route-level admin
subscreens. That broader Admin Console is not the current-phase target. In the
current phase, separate Admin Console / Jobs remains out of top-level UI, and
Settings absorbs only the setup/access responsibilities needed before module
delivery resumes.

## Runtime Coverage Accepted

- Settings scope authority exposes setup counts, active context, blocker
  reasons, setup visibility, and backend-owned actions.
- Settings access model exposes users, roles, grants, and access policies
  according to the current user's authority.
- Project/client-domain/environment setup is visible in one Settings setup
  surface.
- Grants now include backend-owned binding guidance for user, role, project,
  environment, domain, and active-context match.
- Access policies now include backend-owned binding guidance for project,
  visibility, domain, and active-context match.
- Empty setup states now remain visible and show recovery blockers instead of
  collapsing the setup surface.
- Settings has a visible `Return to Cockpit` route recovery path.

## Evidence

Automated validation:

```text
tests/test_operational_context.py
frontend/src/app/App.test.tsx - Settings tests
frontend production build
git diff --check
```

Browser QA evidence:

```text
var/qa/settings-policy-binding-review.png
var/qa/settings-grant-binding-review.png
var/qa/settings-setup-recovery-empty.png
```

Supporting docs:

```text
docs/agent/TASK_CONTRACT_SETTINGS_POLICY_BINDING_UX.md
docs/agent/TASK_CONTRACT_SETTINGS_ROLE_GRANT_REVIEW_UX.md
docs/agent/TASK_CONTRACT_SETTINGS_SETUP_RECOVERY_UX.md
docs/agent/VALIDATION_REPORT.md
```

## Non-Blocking Follow-Ups

- Normal non-admin users with no setup authority can hit `Settings is
  unavailable` because audit/feature-flag side queries return `403`. This is a
  scoped-read hardening follow-up, not a blocker for DBA/project-admin setup
  flows.
- `AdminConsoleView` remains the component name even though the visible module
  is Settings. Rename only in a deliberate route/component cleanup slice.
- Route-level detail/edit/retire screens for setup objects remain future
  Settings route-family work.
- OTM connection governance, feature flag impact/history, audit search, and
  jobs detail remain outside the current Settings phase.

## Blocking Gaps

No blocking Settings gaps remain for the current To-Be adaptation sequence.

## Handoff Decision

Settings can hand off to the next module. The next recommended module slice is
Rates Studio completion against `10 / Rates Studio Deep Flow`.
