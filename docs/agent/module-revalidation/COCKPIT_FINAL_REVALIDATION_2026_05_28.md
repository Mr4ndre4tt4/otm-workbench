# Cockpit Final Revalidation

**Status:** accepted for current UI phase
**Date:** 2026-05-28
**GitHub issue:** #186

## Scope Decision

Project Cockpit is accepted for the current UI phase as a compact authenticated
hub with:

- Context Selector;
- Public View state;
- Project Info;
- accelerator launch cards;
- visible route recovery back to Cockpit;
- backend-owned context, availability, disabled reasons, permissions, and
  scope behavior.

The current accepted scope follows `AGENTS.md`, `CURRENT_SCOPE.md`, and the
Project Cockpit v3 wireframe brief. The older consolidated Cockpit spec still
contains command-center/project-management wording, but readiness, workstream,
blocker, job, activity, and evidence dashboards are not part of the current
top-level Cockpit acceptance target.

## Runtime Coverage Accepted

- `/home` renders Project Cockpit with Context Selector, Project Info, and
  Accelerators as the primary macro groups.
- Public View is represented as a context state, not as a separate sidebar
  route.
- Private context selection persists through backend active-context contracts.
- Accelerators open allowed active UI phase modules and preserve route recovery
  back to Cockpit.
- Missing/private context disables private accelerators with backend-owned
  disabled reasons.
- DBA and scoped-user visibility are explicit in backend summary behavior.
- Stale active contexts are ignored after grant changes.
- Unknown or unavailable routes recover through the module-unavailable state
  with a visible return path.

## Evidence

Fresh automated validation on 2026-05-28:

```text
tests/test_project_cockpit_summary.py + tests/test_modules_navigation.py: 17 passed
App.test.tsx - Cockpit: 1 passed
AppFunctionalShell.test.tsx - persists backend-owned context: 1 passed
```

Existing browser QA evidence from the Cockpit v3 completion slice:

```text
var/qa/cockpit-public-view.png
var/qa/cockpit-private-scope-viewport.png
var/qa/cockpit-scoped-user.png
var/qa/cockpit-route-recovery.png
```

Supporting docs:

```text
docs/agent/TASK_CONTRACT_COCKPIT_DEEP_FLOW_COMPLETION.md
docs/superpowers/plans/2026-05-27-cockpit-deep-flow-completion.md
docs/agent/VALIDATION_REPORT.md
```

## Non-Blocking Follow-Ups

- The older consolidated Cockpit spec should eventually be rewritten or marked
  superseded where it describes project-management dashboards as the next
  direction.
- Any future secure-vault reveal behavior requires a dedicated security design
  before implementation.
- Fresh browser QA may be rerun if the shell/assistant parallel work changes
  the authenticated shell layout.

## Blocking Gaps

No blocking Cockpit gaps remain for the current To-Be adaptation sequence.

## Handoff Decision

Close #186. The next recommended tracked issue is #187 Rates Studio
revalidation against the active To-Be flow.
