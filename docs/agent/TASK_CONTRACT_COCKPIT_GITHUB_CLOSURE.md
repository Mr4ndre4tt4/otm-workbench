# Task Contract: Cockpit GitHub Closure

**Date:** 2026-05-28
**Status:** implementation complete

## Objective

Revalidate and close GitHub issue #186 for the current Project Cockpit v3
scope: Context Selector, Project Info, Public View state, and accelerator
launcher without project-management dashboard behavior.

## Original User Request

The user asked to continue with the next roadmap step after closing Settings
#185.

## Interpreted Scope

- Confirm that the existing Cockpit v3 implementation and evidence still match
  the current governance scope.
- Run fresh automated validation for backend summary, current-phase navigation,
  Cockpit UI, and context/accelerator navigation.
- Record a current closure note and close #186.

## Out Of Scope

- New Cockpit product implementation.
- Reintroducing readiness, workstream, blocker, job, activity, or evidence
  dashboard panels into Cockpit.
- Updating Integration Mapping, Assistant, or shell work from parallel
  workstreams.
- Fresh browser screenshot capture, because existing browser evidence already
  records the Cockpit v3 acceptance states and this slice is GitHub/docs
  closure plus automated revalidation.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_COCKPIT_GITHUB_CLOSURE.md`
- `docs/agent/module-revalidation/COCKPIT_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping files.
- Workbench Assistant files.
- frontend shell files currently modified by a parallel workstream.

## Acceptance Criteria

- Fresh backend/nav validation passes.
- Fresh Cockpit frontend validation passes.
- Fresh functional shell context persistence validation passes.
- Existing browser QA evidence is named and tied to the closure.
- #186 is updated and closed without changing product behavior.

## Validation Plan

```powershell
python -m pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Cockpit"
npm test -- src/app/AppFunctionalShell.test.tsx -t "persists backend-owned context"
```

## Risks

- The older consolidated Project Cockpit spec still contains command-center
  wording. The accepted current-phase scope comes from `AGENTS.md`,
  `CURRENT_SCOPE.md`, and the v3 wireframe brief.
- Parallel shell/assistant changes are present in the worktree and must not be
  committed as part of this closure.

## Decision

Proceed with documentation/GitHub closure only. The next tracked implementation
issue after #186 should be #187 Rates revalidation.
