# Project Cockpit v3 Penpot Creation Report

**Status:** created and read back from Penpot
**Date:** 2026-05-26
**Module:** Shell / Login / Logout / Project Cockpit v3

## Target

```text
file: otm-workbech-new-wireframe
file-id: e7a86fff-661d-81c1-8008-14af24af603d
page: 01C Shell Context Selector Cockpit v3
page-id: 575775e8-ca97-8021-8008-14ec4ed580d8
```

Penpot page URL:

```text
https://design.penpot.app/#/workspace?team-id=e7a86fff-661d-81c1-8008-148fafe68f60&file-id=e7a86fff-661d-81c1-8008-14af24af603d&page-id=575775e8-ca97-8021-8008-14ec4ed580d8
```

## v3 Direction

Project Cockpit v3 removes the extra route-level boards from v2.1:

- no `Client Overview` screen;
- no `Public View` screen;
- no `Project Info` screen or sidebar item.

The authenticated Cockpit is a single screen with three macro groups:

- `Context Selector`: defines Public vs Client/domain and environment;
- `Project Info`: useful URLs, docs, contacts, and secure-vault metadata inside
  Cockpit;
- `Accelerators`: module entry cards.

The sidebar contains only Cockpit, accelerators, Admin, and Dev Tools.

## Boards Created

| Board | Route | State | Child count | Marker | Revision |
|---|---|---|---:|---|---|
| `SHELLV3-00 Navigation map` | `wireframe map` | `navigation-map` | 31 | `project-cockpit-shell-v3` | `v3-single-cockpit` |
| `SHELLV3-01 Login` | `/login` | `unauthenticated` | 19 | `project-cockpit-shell-v3` | `v3-single-cockpit` |
| `SHELLV3-02 Logout or session ended` | `/logout` | `signed-out` | 18 | `project-cockpit-shell-v3` | `v3-single-cockpit` |
| `SHELLV3-03 Project Cockpit` | `/home` | `active-context` | 121 | `project-cockpit-shell-v3` | `v3-single-cockpit` |

## Old Penpot Boards Removed

The Penpot plugin does not expose direct page deletion. Old generated pages
were renamed and their generated boards were removed:

| Page | Result |
|---|---|
| `zz superseded empty - Project Cockpit v1` | 14 generated `SHELL-xx` boards removed |
| `zz superseded empty - Project Cockpit v2.1` | 7 generated `SHELLV2-xx` boards removed |

## Validation Evidence

Readback from Penpot confirmed:

- active page id is `575775e8-ca97-8021-8008-14ec4ed580d8`;
- active page name is `01C Shell Context Selector Cockpit v3`;
- active board count is `4`;
- all 4 active boards are marked with `project-cockpit-shell-v3`;
- all 4 active boards are marked with revision `v3-single-cockpit`;
- old v1 and v2.1 generated boards were removed.

## Next Step

Run user/Michelangelo visual review on v3, focusing on the single Cockpit
composition, context selector clarity, sidebar scope, and Project Info security
boundary.
