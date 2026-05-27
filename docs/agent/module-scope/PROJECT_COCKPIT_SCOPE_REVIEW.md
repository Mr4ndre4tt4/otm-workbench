# Shell / Project Cockpit Scope Review

**Status:** revised for v3 single-cockpit scope, context isolation, and shell navigation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_PROJECT_COCKPIT_CONSOLIDATED_SPEC.md`

## 1. Revised Intent

Project Cockpit is not a project-management dashboard and should not try to
control the implementation lifecycle. OTM Workbench is a set of accelerators
that can be used at the beginning, middle, or end of a project, in whichever
order the consultant needs.

The Cockpit should act as:

- a context selector;
- an accelerator launcher;
- a project information hub;
- a safe entry/exit shell for login, logout, and session recovery.

It must not force readiness, workstream, blocker, job, or activity workflows
onto the user.

## 2. Product Rule: Data Isolation First

Every persisted operational record must be classified by:

```text
client/domain + environment + visibility/access policy
```

The intent is similar to an OTM VPD/domain-grant model:

- users see only records allowed by their client/domain, environment, and role;
- `DBA` has full visibility across client/domain and environment scopes;
- normal users operate inside an explicit active context;
- `Public View` is a controlled shared scope for reusable assets, not a place
  where client data becomes public.

## 3. Admin Ownership

Admin owns setup and access governance:

- create and maintain clients/domains;
- create and maintain environments such as `DEV`, `QAS`, and `PROD`;
- configure users, roles, grants, and access policies;
- manage who can see public/shared assets, copy assets, or administer secrets.

The Cockpit may show context selectors and access state, but it does not create
clients/domains, environments, roles, or grants.

## 4. Validated Target Scope

Project Cockpit v3 includes:

- navigation map for the wireframe review;
- `/login`;
- `/logout` or session-ended state;
- `/home` single Cockpit containing Context Selector, Project Info, and
  Accelerators.

The Cockpit does not include separate `Client Overview`, `Public View`, or
`Project Info` shell routes. Public vs client/domain scope is selected inside
the Context Selector macro group.

## 5. Project Info Hub

Project Info inside Cockpit may include:

- useful URLs grouped by environment;
- OTM environment links;
- project documentation links;
- runbooks and operational notes;
- contacts and ownership notes;
- credential/vault placeholders.

Credential display is intentionally not solved in the wireframe. It requires a
separate security decision before implementation:

- encrypted storage;
- per-secret permissions;
- reauthentication before reveal;
- audit trail;
- no secret values in logs, docs, fixtures, screenshots, or seeds.

## 6. Explicit Non-Scope

- Do not become a full project control surface.
- Do not force module order or phase readiness.
- Do not model workstreams, blockers, activity timelines, or job dashboards in
  the Cockpit.
- Do not duplicate Admin setup screens.
- Do not expose secrets directly in wireframes, docs, tests, or screenshots.
- Do not mix private client/domain data into `Public View`.
- Do not make module entry depend on artificial project phase gates.

## 7. Cleanup Watchlist

Remove or demote from Cockpit scope:

- readiness dashboards;
- workstream dashboards;
- blocker dashboards;
- activity timeline;
- jobs summary;
- global action destination review;
- any workflow that implies OTM Workbench controls the whole project.

Keep:

- login/logout/session recovery;
- persistent authenticated sidebar;
- top-right Light/Dark toggle, user menu, and Logout;
- visible entry paths between shell states;
- context selector;
- environment selector;
- public/shared assets entry;
- accelerator launcher;
- project info macro group.

## 8. Backend Contract Dependencies

- authentication/session state;
- active context: client/domain, environment, public/private scope;
- available accelerator modules by role/context;
- user grants and roles;
- domain/environment visibility filters;
- public/shared asset visibility;
- project info records by client/domain and environment;
- secure secret metadata without exposing secret values.

## 9. Acceptance For Wireframe Phase

The module can move forward when the Penpot v3 board set shows:

- route arrows and entry-path notes that explain how each shell/state is
  reached;
- login and logout/session-ended states;
- persistent sidebar and top-right account/theme controls on authenticated
  boards;
- active Context Selector for Public vs client/domain and environment;
- accelerator cards that are available without project-phase gating;
- Project Info macro group inside Cockpit with secure-vault placeholder;
- Admin-owned setup clearly outside Cockpit.
