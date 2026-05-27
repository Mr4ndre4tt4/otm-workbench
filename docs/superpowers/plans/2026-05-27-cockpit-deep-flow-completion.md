# Cockpit Deep Flow Completion Plan

## Goal

Complete Project Cockpit as the approved v3 single-screen hub: Context
Selector, Project Info, and Accelerators, with Public View as a scope state and
without dashboard panels for readiness, workstreams, blockers, jobs, evidence,
or activity.

## References

- `AGENTS.md`
- `docs/agent/TASK_CONTRACT_COCKPIT_DEEP_FLOW_COMPLETION.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`
- `tests/test_project_cockpit_summary.py`
- `frontend/src/app/routes/WorkbenchRoute.tsx`

## Task 1 - Lock Backend Cockpit Contract Tests

- [x] Extend `tests/test_project_cockpit_summary.py` so the summary payload
  exposes the v3 groups required by the UI:
  - `context_selector`;
  - `project_info`;
  - `accelerators`;
  - `user_scope`;
  - `route_recovery`.
- [x] Assert that no raw job input, artifact file path, evidence unsafe summary,
  secret value, or private hidden-scope record appears in the payload.
- [x] Assert empty/no-context behavior:
  - Context Selector action enabled;
  - private-context accelerators disabled with `ACTIVE_CONTEXT_REQUIRED`;
  - Settings setup link/action available when setup is incomplete.
- [x] Assert active private-context behavior:
  - active project/profile/environment/domain is represented;
  - accelerators for active UI phase modules are visible;
  - disabled accelerators include backend-owned disabled reasons.
- [x] Assert Public View behavior:
  - Public scope is represented as selector state;
  - private client/domain records are absent;
  - Public View is not represented as a separate navigation route.
- [x] Assert DBA behavior:
  - DBA visibility is explicit;
  - DBA state does not become the normal user default.
- [x] Assert stale grant behavior continues to clear the active context.

## Task 2 - Update Backend Cockpit Payload

- [x] Update `src/otm_workbench/platform/routes.py` in
  `project_cockpit_summary_payload` to return the v3 groups from Task 1.
- [x] Keep backend-owned action objects for setting context, launching active
  modules, opening Settings setup, and recovering from blocked routes.
- [x] Use existing navigation and capability contracts for accelerator labels,
  icons, hrefs, statuses, and disabled reasons.
- [x] Keep recent jobs, recent artifacts, and recent evidence out of the
  primary Cockpit content contract; expose only safe links/actions if needed.
- [x] Preserve existing scope filtering through `can_use_active_context`,
  `apply_job_visibility`, and operational scope utilities.

## Task 3 - Update Frontend Types And Cockpit UI

- [x] Update `frontend/src/platform/types/cockpit.ts` for the new v3 summary
  shape.
- [x] Refactor `CockpitContent` in
  `frontend/src/app/routes/WorkbenchRoute.tsx` so `/home` renders:
  - Context Selector;
  - Project Info;
  - Accelerators.
- [x] Remove primary Cockpit rendering of metric grids, readiness panel, recent
  jobs, and recent evidence.
- [x] Keep `ContextSummary` and `ContextSwitcher` only where they support the
  approved selector flow.
- [x] Ensure each accelerator has a visible route target, disabled state, and
  return path when blocked.
- [x] Add or adjust CSS in `frontend/src/ui/layouts.css` only as needed for
  consistent spacing, responsive wrapping, and visual polish.

## Task 4 - Lock Frontend Tests

- [x] Update Cockpit mocks in `frontend/src/app/App.test.tsx` to match the v3
  backend contract.
- [x] Add assertions for Context Selector, Project Info, Accelerators, Public
  View state, and disabled accelerator reasons.
- [x] Add assertions that removed dashboard labels do not appear as primary
  Cockpit sections:
  - Recent jobs;
  - Recent evidence;
  - Project activity;
  - readiness/workstream/blocker language.
- [x] Keep route tests for unknown or unavailable modules.

## Task 5 - Run Automated Validation

- [x] Run `pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q`.
- [x] Run `npm test -- src/app/App.test.tsx -t "Cockpit"` from `frontend`.
- [x] Run `git diff --check` on changed files.

## Task 6 - Browser QA And Evidence

- [x] Start or reuse the frontend dev server.
- [x] Open `/home` in browser QA.
- [x] Validate no-context Cockpit.
- [x] Validate active private-context Cockpit.
- [x] Validate Public View selector state.
- [x] Validate normal-user restricted visibility.
- [x] Validate DBA visibility.
- [x] Validate accelerator launch and return path.
- [x] Validate unknown-route recovery.
- [x] Capture screenshots for meaningful states and reference them in the
  validation report.

## Task 7 - Documentation And Handoff

- [x] Update `docs/agent/VALIDATION_REPORT.md` with commands, outputs, browser
  QA notes, and screenshots.
- [x] Update `docs/agent/HANDOFF.md` with Cockpit completion status, remaining
  risks, and next module recommendation.
- [x] Update `docs/agent/DECISION_LOG.md` if any scope decision changes.
  Reviewed; no new scope decision was introduced in this QA step.
- [x] Update `docs/agent/RISK_REGISTER.md` if secure-vault metadata, Public
  View, or DBA visibility risks change.
  Reviewed; the existing secure-vault risk remains unchanged.

## Stop Conditions

- Stop before adding secret retrieval or displaying secret values.
- Stop before creating separate Client Overview, Public View, or Project Info
  routes.
- Stop before turning Cockpit into a jobs/evidence/readiness/workstream
  dashboard.
- Stop if a required scope rule conflicts with existing runtime behavior and
  needs product decision.
