# Project Cockpit Penpot Creation Report

**Status:** created and read back from Penpot
**Date:** 2026-05-26
**Module:** Shell / Login / Logout / Project Cockpit

## Target

```text
file: otm-workbech-new-wireframe
file-id: e7a86fff-661d-81c1-8008-14af24af603d
page: 01 Shell, Login, Logout, and Project Cockpit
page-id: e7a86fff-661d-81c1-8008-14af24af603e
```

## Creation Method

The standard `mcp__penpot__` wrapper remained unreliable in this conversation,
so the boards were created through the validated direct JSON-RPC path described
in `docs/agent/PENPOT_CONNECTOR_DIAGNOSTIC.md`.

The first large creation attempt exceeded the Penpot task timeout. The final
creation was performed in seven batches of two boards each.

During the process, the MCP session temporarily pointed to the older
`otm-workbench` file. No Project Cockpit boards were created there. The page
name touched during that check was restored to `Page 1` before continuing.

## Boards Created

| Board | Child count | Marker |
|---|---:|---|
| `SHELL-01 Login` | 24 | `project-cockpit-shell` |
| `SHELL-02 Login invalid credentials` | 26 | `project-cockpit-shell` |
| `SHELL-03 Logout confirmed` | 19 | `project-cockpit-shell` |
| `SHELL-04 Signed-out recovery` | 21 | `project-cockpit-shell` |
| `SHELL-05 No active project` | 46 | `project-cockpit-shell` |
| `SHELL-06 Context setup` | 54 | `project-cockpit-shell` |
| `SHELL-07 Project Cockpit ready` | 62 | `project-cockpit-shell` |
| `SHELL-08 Readiness blocked` | 54 | `project-cockpit-shell` |
| `SHELL-09 Workstreams` | 51 | `project-cockpit-shell` |
| `SHELL-10 Blockers` | 54 | `project-cockpit-shell` |
| `SHELL-11 Activity timeline` | 51 | `project-cockpit-shell` |
| `SHELL-12 Jobs summary failed` | 54 | `project-cockpit-shell` |
| `SHELL-13 Artifacts and evidence permissions` | 51 | `project-cockpit-shell` |
| `SHELL-14 Global action destination review` | 54 | `project-cockpit-shell` |

Total root boards in the target page after creation:

```text
14
```

## Scope Covered

- login default;
- invalid login credentials;
- logout confirmed;
- signed-out recovery;
- no active project;
- context setup;
- ready Project Cockpit;
- readiness blocked;
- workstreams;
- blockers;
- activity timeline;
- failed jobs summary;
- artifacts/evidence permission state;
- global action destination review.

## Validation Evidence

Readback from Penpot confirmed:

- connected file id is `e7a86fff-661d-81c1-8008-14af24af603d`;
- connected page id is `e7a86fff-661d-81c1-8008-14af24af603e`;
- page name is `01 Shell, Login, Logout, and Project Cockpit`;
- root board count is `14`;
- every board is a Penpot `board`;
- every board is marked with `project-cockpit-shell`.

## Next Step

Run user/Michelangelo visual review on the Project Cockpit board set. After
approval, continue to Master Data / Data Factory in the approved Penpot order.
