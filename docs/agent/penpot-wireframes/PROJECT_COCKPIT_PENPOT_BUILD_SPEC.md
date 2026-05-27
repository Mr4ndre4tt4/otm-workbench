# Project Cockpit Penpot Build Spec

**Status:** created in Penpot and ready for visual review
**Date:** 2026-05-26
**Module:** Shell / Login / Logout / Project Cockpit
**Source scope review:** `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
**Source wireframe brief:** `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`

## 1. Penpot Status

Direct Penpot creation through the standard `mcp__penpot__` wrapper was
attempted on 2026-05-26, but the wrapper failed with a transport
deserialization error. A manual JSON-RPC diagnostic confirmed that the
underlying Penpot MCP endpoint, target file, target page, overview tool, and
execute_code tool work.

This build spec was used to create the Project Cockpit Penpot boards through
the validated JSON-RPC path described in
`docs/agent/PENPOT_CONNECTOR_DIAGNOSTIC.md`.

Creation report:

```text
docs/agent/penpot-wireframes/PROJECT_COCKPIT_PENPOT_CREATION_REPORT.md
```

## 2. Target Page

```text
01 Shell, Login, Logout, and Project Cockpit
```

Target file:

```text
https://design.penpot.app/#/workspace?team-id=e7a86fff-661d-81c1-8008-148fafe68f60&file-id=e7a86fff-661d-81c1-8008-14af24af603d&page-id=e7a86fff-661d-81c1-8008-14af24af603e
```

## 3. Wireframe Intent

The Cockpit is a command center and safety layer, not a decorative dashboard.
The first viewport must answer:

- who is signed in;
- what project/context is active;
- whether the project is ready;
- what is blocked;
- what the safest next action is.

Login, logout, and session recovery are first-class shell states. Authenticated
module actions must not appear available after logout or invalid session.

## 4. Frame Set

Recommended low-fidelity frame size:

```text
1440 x 1024
```

Recommended frame names:

```text
SHELL-01 Login
SHELL-02 Login invalid credentials
SHELL-03 Logout confirmed
SHELL-04 Signed-out recovery
SHELL-05 No active project
SHELL-06 Context setup
SHELL-07 Project Cockpit ready
SHELL-08 Readiness blocked
SHELL-09 Workstreams
SHELL-10 Blockers
SHELL-11 Activity timeline
SHELL-12 Jobs summary failed
SHELL-13 Artifacts and evidence permissions
SHELL-14 Global action destination review
```

## 5. Shared Patterns

Use low-fidelity grayscale components. Do not recreate current implementation
styling.

### Auth Shell

- product mark placeholder;
- environment label;
- sign-in form;
- inline validation slot;
- recovery/help link;
- no authenticated navigation.

### Authenticated Shell

- compact top bar with active project, user, environment, and sign out;
- left module navigation with backend-owned capability visibility;
- disabled nav items include a visible reason;
- content area uses route-level headers and visible return paths.

### Context Bar

- active project;
- profile;
- environment;
- data set or scope;
- readiness state;
- last refresh;
- primary safe action.

### Readiness Strip

- status: ready, blocked, incomplete, or unavailable;
- blocker count;
- next required action;
- owning route.

### Blocker Summary

- blocker title;
- severity;
- owner;
- affected route/module;
- action;
- reason when action is disabled.

## 6. Frame Details

### SHELL-01 Login

Route: `/login`

Purpose:
Allow a user to start safely without authenticated navigation visible.

Visible regions:

- centered login form;
- environment selector or label;
- credential fields;
- sign-in action;
- help/recovery link;
- version/build label.

Primary acceptance:
No module navigation or project action appears before authentication.

### SHELL-02 Login invalid credentials

Route: `/login`

Purpose:
Show a failed sign-in without losing context or implying account state beyond
what the backend returns.

Visible regions:

- same login form as `SHELL-01`;
- inline error summary near the form;
- field-level invalid state;
- retry action;
- recovery/help link.

Primary acceptance:
Error copy is clear, non-leaky, and keyboard focus returns to the actionable
area.

### SHELL-03 Logout confirmed

Route: `/logout`

Purpose:
Confirm that the session ended and remove all authenticated actions.

Visible regions:

- session-ended message;
- signed-out status;
- return to login action;
- optional last environment label;
- no module navigation.

Primary acceptance:
The screen cannot be mistaken for an authenticated shell route.

### SHELL-04 Signed-out recovery

Route: any authenticated route after expired session

Purpose:
Handle route recovery when the user lands on a protected route without a valid
session.

Visible regions:

- protected-route notice;
- original route label;
- return to login action;
- short explanation that work was not executed;
- no module actions.

Primary acceptance:
The user understands why they were stopped and how to resume.

### SHELL-05 No active project

Route: `/home`

Purpose:
Show authenticated shell without active project context.

Visible regions:

- top bar with signed-in user and environment;
- disabled module navigation with reasons;
- context setup prompt;
- recent projects or create/select project action;
- blocker panel explaining missing context.

Primary acceptance:
No operational module appears ready when project context is missing.

### SHELL-06 Context setup

Route: `/home/context`

Purpose:
Let the user select or repair project, profile, environment, and work scope.

Visible regions:

- context form;
- validation summary;
- project selector;
- profile/environment selectors;
- save and cancel/return actions;
- downstream readiness preview.

Primary acceptance:
The user can see which context fields gate module access.

### SHELL-07 Project Cockpit ready

Route: `/home`

Purpose:
Provide the main ready-state cockpit.

Visible regions:

- context bar;
- readiness strip;
- next safe action;
- workstream status summary;
- blocker summary;
- activity summary;
- jobs/artifacts/evidence shortcuts;
- backend-owned global actions.

Primary acceptance:
The first viewport makes context, readiness, blocker count, and next action
obvious.

### SHELL-08 Readiness blocked

Route: `/home/readiness`

Purpose:
Explain why the project is not ready and what must happen next.

Visible regions:

- context bar;
- readiness score/status;
- blocker list grouped by owner or route;
- disabled action reasons;
- retry/recheck action;
- return to cockpit.

Primary acceptance:
The user can identify the blocking condition before clicking into modules.

### SHELL-09 Workstreams

Route: `/home/workstreams`

Purpose:
Show module/workstream progress without becoming the module itself.

Visible regions:

- workstream table;
- status, owner, next action, last activity;
- module entry action;
- disabled reason when gated;
- filter chips.

Primary acceptance:
Each workstream has a visible destination or a visible reason it is blocked.

### SHELL-10 Blockers

Route: `/home/blockers`

Purpose:
Make cross-module blockers inspectable and actionable.

Visible regions:

- blocker list/table;
- severity and owning module;
- dependency and affected route;
- action path;
- resolution state;
- return to cockpit.

Primary acceptance:
Critical blockers have clear ownership and next action.

### SHELL-11 Activity timeline

Route: `/home/activity`

Purpose:
Show recent project events without replacing Evidence Hub.

Visible regions:

- timeline;
- event type, actor, timestamp;
- related module;
- linked artifact/evidence when available;
- empty state for no activity.

Primary acceptance:
Timeline entries link to owning routes where detail belongs.

### SHELL-12 Jobs summary failed

Route: `/home/jobs`

Purpose:
Summarize job health and route failed jobs to Admin Console / Jobs.

Visible regions:

- job status strip;
- failed job card/table row;
- retry eligibility;
- owner route;
- view job detail action;
- return to cockpit.

Primary acceptance:
The Cockpit identifies the failed job but does not duplicate the Admin job
detail screen.

### SHELL-13 Artifacts and evidence permissions

Routes: `/home/artifacts`, `/home/evidence`

Purpose:
Summarize available artifacts/evidence and show permission-aware unavailable
states.

Visible regions:

- artifact/evidence summary cards;
- latest generated artifact;
- unavailable-by-permission state;
- owning Evidence Hub route link;
- request access or contact owner action.

Primary acceptance:
Permission limits are visible and do not look like missing data.

### SHELL-14 Global action destination review

Route: `/home/actions`

Purpose:
Expose backend-owned global actions and their destinations before cleanup.

Visible regions:

- global action list;
- destination route;
- prerequisite;
- disabled reason;
- destructive/critical flag;
- owner module.

Primary acceptance:
Every global action has a visible destination, prerequisite, and enabled or
disabled state.

## 7. Michelangelo Acceptance Checklist

- Login and logout/session-ended states are represented.
- Authenticated navigation is absent after logout or invalid session.
- Active context is visible in every authenticated frame.
- Blocked and missing-context states explain the prerequisite.
- Module shortcuts are backend-owned and permission aware.
- Global actions show destination routes.
- Cockpit summaries do not duplicate module detail screens.
- Empty, failed, blocked, and permission-unavailable states are visible.
- Return paths are present on child routes.

## 8. Next Build Step

Run a Michelangelo/user visual review against the resulting Penpot boards, then
apply accepted corrections before moving to the next module.
