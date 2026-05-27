# Michelangelo Wireframe Brief - Shell / Project Cockpit v3

**Status:** revised for Figma v3 single-cockpit model
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Authentication/session shell and single authenticated Cockpit with context
selector, project information, and accelerator launcher.

Primary user task:
Sign in, define whether the active context is Public or client/domain scoped,
then use project info or launch the accelerator needed now without being forced
through a project workflow.

User profile:
Functional consultant, implementation lead, admin-adjacent operator, DBA.

Task criticality:
High. Wrong context can expose or modify the wrong client/domain/environment
data.

Input reviewed:
User scope correction, Project Cockpit v1 Figma findings, governance rules,
and module ledger.

Evidence source:
Repository documentation and user direction. The v1 Figma board set is now
superseded as a project-control interpretation.

Assumptions:
Backend owns context, roles, grants, visibility, accelerator availability, and
secure secret metadata.

## 2. Archetypes

- authentication flow;
- context switcher;
- accelerator launcher;
- project information macro group;
- admin-owned setup boundary.

## 3. Route Inventory For Wireframes

```text
/login
/logout
/home
```

## 4. UX Findings To Design Around

ID:
PC2-UX-01

Severity:
P0 Blocker

Category:
Data isolation and context safety

Where:
Global shell and Cockpit.

Evidence:
The product must classify all operational records by client/domain plus
environment and visibility/access policy.

Problem:
If context is hidden or optional, users can work in the wrong client,
environment, or public/private scope.

User impact:
Wrong data changes, accidental exposure, and loss of trust.

Recommendation:
Make Public vs client/domain and environment visibly selected before module
entry. Show the active context in the shell.

Implementation hint:
Use a compact context bar and context selector section. Backend returns allowed
contexts and roles.

Acceptance criteria:
Every module launch starts from the single Cockpit after an explicit active
context is selected.

---

ID:
PC2-UX-02

Severity:
P1 High

Category:
Workflow scope

Where:
Cockpit hub.

Evidence:
The user clarified OTM Workbench should group accelerators usable at any
project moment, not control the project lifecycle.

Problem:
Readiness, blocker, workstream, jobs, and activity boards turn the Cockpit into
a project management dashboard.

User impact:
The tool feels overbuilt and constrains how consultants actually use
accelerators.

Recommendation:
Replace project-control surfaces with accelerator cards and simple context
controls.

Implementation hint:
Cards open modules directly when permitted. Disabled cards explain permission
or missing context only, not project phase.

Acceptance criteria:
The Cockpit does not imply a required module order or project phase.

---

ID:
PC2-UX-03

Severity:
P1 High

Category:
Security and sensitive information

Where:
Project Info Hub credential/vault area.

Evidence:
The user wants useful project info including URLs, docs, and possibly
passwords, but passwords require extra security design.

Problem:
Showing or storing secrets casually would create a serious security risk.

User impact:
Credential exposure, audit gaps, and unsafe screenshots/logs.

Recommendation:
Wireframe secrets only as secure metadata and reveal flow placeholder requiring
reauthentication and later security design.

Implementation hint:
Separate secret metadata from encrypted value storage. Add reveal audit and
role checks before implementation.

Acceptance criteria:
No secret value appears in any wireframe; vault reveal is represented as a
blocked/secure placeholder.

---

ID:
PC2-UX-04

Severity:
P1 High

Category:
Navigation and route comprehension

Where:
Project Cockpit v3 board set.

Evidence:
The user clarified that Client Overview, Public View, and Project Info should
not exist as separate sidebar/shell destinations.

Problem:
Extra route-level boards make the Cockpit feel like a workflow router instead
of a compact accelerator home.

User impact:
Reviewers may approve or reject screens without understanding whether they are
main flows, optional child views, or shell states.

Recommendation:
Remove separate Client Overview and Public View boards. Keep Project Info as a
macro group inside the Cockpit only.

Implementation hint:
Use `SHELLV3-03 Project Cockpit` as the only authenticated Cockpit board.
Inside it, show macro groups for Context Selector, Project Info, and
Accelerators.

Acceptance criteria:
No Client Overview, Public View, or Project Info route appears in the sidebar
or active board set.

---

ID:
PC2-UX-05

Severity:
P1 High

Category:
Shell consistency and account controls

Where:
Authenticated boards.

Evidence:
The sidebar disappeared in v2, and top-right controls for Light/Dark mode,
user menu, and Logout were missing.

Problem:
Without persistent shell controls, the wireframe does not describe how users
switch modules, change theme, or safely end the session.

User impact:
The eventual UI can become inconsistent or omit core account/navigation
controls.

Recommendation:
Show the authenticated shell consistently on `SHELLV3-03`: sidebar, active
context, Light/Dark toggle, user menu, and Logout. Keep login/logout screens
free of authenticated navigation.

Implementation hint:
Treat sidebar and top-right account/theme controls as shared shell components,
not module-specific content.

Acceptance criteria:
The single authenticated Cockpit board includes sidebar, active context,
Light/Dark toggle, user menu, and Logout; unauthenticated boards do not show
authenticated navigation.

## 5. Required Wireframe Boards

- `SHELLV3-00 Navigation map`
- `SHELLV3-01 Login`
- `SHELLV3-02 Logout or session ended`
- `SHELLV3-03 Project Cockpit`

## 6. Wireframe Acceptance Criteria

- Active Context Selector defines Public vs client/domain, environment, and
  visibility scope.
- Navigation arrows and entry-path annotations explain how each shell/state is
  reached.
- The authenticated Cockpit includes persistent sidebar, Light/Dark toggle,
  user menu, and Logout.
- Login and logout/session-ended boards hide authenticated navigation.
- Public scope is selected inside Context Selector, not as a sidebar route.
- Module cards are accelerators, not project workflow steps.
- Admin-owned setup is visible only as a link/notice, not embedded setup.
- DBA/full-access behavior is represented as role visibility, not normal user
  default.
- Project Info appears only as a macro group inside Cockpit and shows
  URLs/docs/runbooks/contacts plus a secure vault placeholder.
- No readiness, blocker, workstream, job, activity, or global-action review
  boards remain in the v3 target.

## 7. External Validation Recommended

After Figma v3:

- Michelangelo review for context clarity and over-scoping;
- security review for secret/vault concept before implementation;
- backend contract review for domain/environment filtering and grants;
- browser QA later for context persistence and module-launch filtering.
