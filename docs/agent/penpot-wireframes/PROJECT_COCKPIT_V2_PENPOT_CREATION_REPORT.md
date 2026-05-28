# Project Cockpit v2.1 Penpot Creation Report

**Status:** superseded by Project Cockpit v3; generated boards removed from Penpot
**Date:** 2026-05-26
**Module:** Shell / Login / Logout / Project Cockpit v2.1

## Target

```text
file: otm-workbech-new-wireframe
file-id: e7a86fff-661d-81c1-8008-14af24af603d
page: 01B Shell Context and Accelerator Cockpit v2
page-id: d972a188-a187-8096-8008-14ddc8df1b2f
```

Penpot page URL:

```text
https://design.penpot.app/#/workspace?team-id=e7a86fff-661d-81c1-8008-148fafe68f60&file-id=e7a86fff-661d-81c1-8008-14af24af603d&page-id=d972a188-a187-8096-8008-14ddc8df1b2f
```

## Why v2.1 Exists

The first simplified v2 pass correctly removed project-management overreach,
but it did not make route entry paths explicit enough. The user review raised
four important UX gaps:

- reviewers could not see how to reach each shell/state;
- `SHELLV2-04` and `SHELLV2-05` looked disconnected from the Cockpit;
- `SHELLV2-06` did not show how it is reached;
- authenticated boards were missing persistent sidebar, Light/Dark toggle, user
  menu, and Logout.

v2.1 keeps the simplified Cockpit model and adds navigability, shell
consistency, and account controls.

## Creation Method

The standard `mcp__penpot__` wrapper still failed on
`high_level_overview` with a transport/deserialization error. Creation used the
validated direct JSON-RPC path described in
`docs/agent/PENPOT_CONNECTOR_DIAGNOSTIC.md`.

Before writing, the Penpot session was confirmed against:

```text
file: otm-workbech-new-wireframe
file-id: e7a86fff-661d-81c1-8008-14af24af603d
page: 01B Shell Context and Accelerator Cockpit v2
```

Only boards marked with `project-cockpit-shell-v2` were replaced. The v1 page
and unrelated Penpot work were not touched.

## Boards Created

| Board | Route | State | Child count | Marker | Revision |
|---|---|---|---:|---|---|
| `SHELLV2-00 Navigation map` | `wireframe map` | `navigation-map` | 45 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-01 Login` | `/login` | `unauthenticated` | 22 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-02 Logout or session ended` | `/logout` | `signed-out` | 20 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-03 Context and accelerator cockpit` | `/home` | `active-context` | 127 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-04 Client environment overview` | `/home/client-overview` | `client-overview` | 78 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-05 Public View and shared assets` | `/home/public` | `public-view` | 71 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |
| `SHELLV2-06 Project Info Hub` | `/home/project-info` | `project-info` | 86 | `project-cockpit-shell-v2` | `v2.1-navigation-shell` |

Total root boards in the v2 page after revision:

```text
7
```

## Scope Covered

- navigation map with arrows between shell states;
- login with theme toggle and no authenticated navigation;
- logout/session ended with entry path from user menu or session timeout;
- authenticated Cockpit with sidebar, top context bar, Light/Dark toggle, user
  menu, and Logout;
- visible route arrows from Cockpit to Client Overview, Public View, and
  Project Info Hub;
- client environment overview across DEV, QAS, PROD, and all-environment view;
- Public View as separate collaborative scope;
- Project Info Hub for URLs, docs, contacts, and secure vault placeholder;
- no displayed secret values.

## Validation Evidence

Readback from Penpot confirmed:

- connected file id is `e7a86fff-661d-81c1-8008-14af24af603d`;
- connected file name is `otm-workbech-new-wireframe`;
- connected page id is `d972a188-a187-8096-8008-14ddc8df1b2f`;
- connected page name is `01B Shell Context and Accelerator Cockpit v2`;
- root board count is `7`;
- all 7 boards are marked with `project-cockpit-shell-v2`;
- all 7 boards are marked with revision `v2.1-navigation-shell`;
- v1 page `01 Shell, Login, Logout, and Project Cockpit` remains present as a
  superseded reference.

## Next Step

Run user/Michelangelo visual review on v2.1, focusing on route comprehension,
authenticated shell consistency, account/logout behavior, Public View
separation, and Project Info Hub secret-safety boundaries.
