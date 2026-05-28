# OTM Workbench Complete Solution Deep-Flow Report

**Status:** active To-Be visual source
**Date:** 2026-05-27

## Target Figma Artifact

```text
File: OTM Workbench - Complete Solution Mockup
File key: 7AkORIWrjmaOiBBA6cMOj9
URL: https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
Page: 00 Analysis + Visual System
```

## Why This Supersedes The Previous Active Visual Target

The earlier active visual consolidation target was:

```text
OTM Workbench - Consolidated Scope Wireframes
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
```

The user clarified that the correct artifact to update is the Complete Solution
Mockup. The `Consolidated Scope Wireframes` file remains supporting reference
and recovery evidence, but the active To-Be mockup source is now the Complete
Solution Mockup.

## Boards Created

Seven deep-flow boards were added to the Complete Solution Mockup:

| Board | Scope |
|---|---|
| `10 / Rates Studio Deep Flow` | Batch search, creation, staging, validation, CSV preview, export, approval, evidence, and Load Plan handoff. |
| `11 / Assets Library Deep Flow` | Asset library, create/detail/edit, versions, links, classifications, guarded download, archive, and Public View boundary. |
| `12 / Load Plan Deep Flow` | Package library/detail, checklist, readiness, CSVUTIL builder, ZIP review, sequence, exports, go/no-go, and handoff. |
| `13 / Order Release Deep Flow` | Template creation/detail/versioning, batch creation/detail, row editor, preview blockers, XML artifacts, and submit readiness. |
| `14 / Integration Mapping Deep Flow` | Definition creation/detail, systems, payloads/schemas, mapping workspace, rules, executable review, preview, spec, and artifacts. |
| `15 / Configuration Settings Deep Flow` | Settings hub, setup library, project detail, client/domain, environments, profiles, users, roles, grants, access policies, and audit. |
| `16 / Cockpit v3 Deep Flow` | Login/session, context selector, Public View, accelerator launcher, permissions, project info, user menu, DBA visibility, and route recovery. |

## Validation Result

Final double check passed in Figma:

```text
allPass: true
boards: 7
screen cards per board: 16
total screen cards: 112
accent rails per board: 16
card overlaps: 0
text overflow: 0
button pairs per board: 16 primary + 16 secondary
grid spacing: 34px horizontal and 34px vertical
font family: IBM Plex Sans
```

## Design Guardrails Captured

- No real client data appears in the mockups.
- Each flow keeps visible return paths through `Back`, `Cancel`, `Home`,
  `Library`, or equivalent recovery actions.
- Empty, blocked, guarded, permission, preview, artifact, and route-recovery
  states are represented.
- Settings owns project, client/domain, environment, user, role, grant, and
  access-policy setup for the current UI phase.
- Cockpit remains a context selector, accelerator launcher, Public View entry,
  and project-info hub. It is not a project-management, readiness, workstream,
  blocker, activity, or jobs dashboard.
- Public View is a separate shared scope, not a shortcut into private
  client/domain data.
- `DBA` visibility is explicit; normal users remain restricted to allowed
  scopes.

## Implementation Use

Use these boards as the To-Be UX reference for implementation planning. They do
not by themselves approve source-code deletion or route removal. Cleanup still
requires route/component inventory, tests, and explicit approval.
