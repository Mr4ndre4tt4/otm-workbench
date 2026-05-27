# Task Contract - Cockpit Deep Flow Completion

## Objective

Bring Project Cockpit from the current scoped-summary implementation to the
approved v3 deep-flow target: one authenticated `/home` screen that acts as
context selector, project-info hub, Public View entry, and accelerator launcher
for the active UI phase modules.

## Original User Request

Continue the next delivery step after consolidating Figma mockups, wireframes,
specs, flows, documentation, context/domain segregation, and operational module
scope locks. The user suggested finishing modules in sequence, with Settings
and Cockpit before Rates, Assets, Master Data, Integration, and Order Release.

## Interpreted Scope

- Revalidate Project Cockpit against the v3 Figma deep-flow direction and
  current repository governance.
- Preserve a single authenticated `/home` route for Cockpit.
- Replace Cockpit dashboard behavior with three macro groups:
  - Context Selector;
  - Project Info;
  - Accelerators.
- Represent Public View as a selectable scope/state inside Context Selector,
  not as a sidebar route.
- Keep module launch cards as accelerators, not ordered workflow stages.
- Keep backend-owned labels, capabilities, status, disabled reasons, and
  available actions.
- Keep all displayed data scoped by client/domain, environment, visibility, and
  access policy.
- Add tests and browser QA for happy, negative, stale-context, permission, DBA,
  Public View, route-recovery, and module-launch paths.

## Out Of Scope

- Creating a separate Client Overview route.
- Creating a separate Project Info route.
- Creating a separate Public View route.
- Reintroducing readiness, workstream, blocker, activity, jobs, evidence, or
  project-management dashboard panels into Cockpit.
- Showing secret values or client data in Project Info, fixtures, docs,
  screenshots, or tests.
- Broad redesign of non-Cockpit modules.
- Deleting, archiving, or mass-moving repository files.
- Changing Figma unless the user explicitly requests another design pass.

## Allowed Files And Areas

- `docs/agent/TASK_CONTRACT_COCKPIT_DEEP_FLOW_COMPLETION.md`
- `docs/superpowers/plans/2026-05-27-cockpit-deep-flow-completion.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `src/otm_workbench/platform/routes.py`
- `frontend/src/platform/types/cockpit.ts`
- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/src/app/App.test.tsx`
- `frontend/src/ui/layouts.css`
- `tests/test_project_cockpit_summary.py`
- `tests/test_modules_navigation.py`

## Protected Files And Areas

- Real client data, real credentials, and secret values.
- Unrelated module implementations unless needed only for route-launch
  verification.
- Historical docs and generated design files not listed in the allowed scope.
- Any stale or unrelated dirty work already present in the worktree.

## Acceptance Criteria

- Cockpit remains one authenticated `/home` screen.
- Cockpit renders Context Selector, Project Info, and Accelerators as the main
  content groups.
- Public View is represented as context/scope state.
- Project Info may show URLs, docs, contacts, and secure-vault metadata, but no
  secret values.
- Accelerators launch only active UI phase modules and expose disabled states
  from backend-owned permissions/context.
- Normal users see only allowed client/domain/environment scopes.
- DBA visibility is explicit and tested.
- Stale active contexts are ignored after grant changes.
- Unknown or blocked routes recover to a clear route-level state with a visible
  return path.
- No readiness, blocker, workstream, jobs, activity, or global dashboard panels
  remain in the Cockpit target.

## Validation Plan

- `pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q`
- `npm test -- src/app/App.test.tsx -t "Cockpit"` from `frontend`
- Browser QA for `/home`, no-context state, active private context, Public View
  state, DBA view, normal-user restricted view, module accelerator launch, and
  unknown-route recovery.
- Screenshot evidence for meaningful Cockpit states after implementation.
- `git diff --check` on changed files.

## Risks

- The older consolidated Cockpit spec may pull implementation back toward a
  command-center or project-management dashboard.
- Existing frontend still shows metrics and recent operational activity, which
  conflicts with the v3 target if left as primary Cockpit content.
- Secure-vault metadata could be mistaken for secret rendering if the contract
  is not strict.
- Public View could become an accidental shortcut into private client/domain
  data if not tested independently.

## Challenge Notes

- Project Cockpit should not solve Settings setup. It may link to Settings when
  setup is missing, but Settings remains the owner of client/domain,
  environment, user, role, grant, and permission setup.
- Jobs, artifacts, and evidence can remain available through backend-owned
  actions or module routes, but Cockpit must not become their dashboard.
- Project Info secure-vault behavior should expose metadata only until a
  separate security design approves secret retrieval.

## Decision

Proceed with a focused Cockpit deep-flow completion slice. The next
implementation step should update the backend contract and frontend Cockpit
screen together, driven by tests that lock the v3 scope.
