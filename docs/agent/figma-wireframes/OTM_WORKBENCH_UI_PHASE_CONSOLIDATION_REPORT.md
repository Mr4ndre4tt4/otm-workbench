# OTM Workbench UI Phase Figma Consolidation Report

**Status:** supporting historical Figma consolidation
**Date:** 2026-05-27

## Supersession Notice

This report documents the earlier Figma consolidation pass in
`OTM Workbench - Consolidated Scope Wireframes`. The active To-Be visual source
is now:

```text
OTM Workbench - Complete Solution Mockup
File key: 7AkORIWrjmaOiBBA6cMOj9
URL: https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
Active page: 00 Analysis + Visual System
```

See:

- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`

## Historical Target Figma Artifact

```text
Project: 606615771
File: OTM Workbench - Consolidated Scope Wireframes
File key: zJGLRJCTArRStISGIPQ2DQ
URL: https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
Active page: Current Scope v2 - Prototype DNA
```

## Reference Figma Artifact

```text
File: OTM Workbench - Complete Solution Mockup
File key: 7AkORIWrjmaOiBBA6cMOj9
URL: https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9
Reference page: 00 Analysis + Visual System
```

## Source Inputs

- User-supplied PDF: `C:/Users/Enzo Trabalho/Downloads/otm-workbench wireframe pdf.pdf`
- Complete Solution Mockup visual system and solution map.
- Current module specs under `docs/otm-workbench/gui/`.
- Current Solon governance docs under `docs/agent/`.

The PDF is image-based, so it was used as visual/layout reference rather than
as extractable text.

## User Calibration

The user selected:

```text
1A: Keep the current eight-module UI phase and only absorb useful
    visual/component patterns from the complete mockup.
2A: Keep the artifact low-fidelity wireframe, not a high-fidelity mockup.
3A: Use the linked Figma mockup as the prototype source.
```

## Active UI Phase Scope

The Figma file consolidates these top-level UI modules:

1. Cockpit
2. Master Data / Data Factory
3. Rates Studio
4. Load Plan / Cutover
5. Integration Mapping Studio
6. Order Release Generator
7. Assets Library
8. Settings

Settings includes project creation, client/domain, environment, profile, user,
role, grant, and access-policy setup.

## Out Of Main UI For Now

- Catalog Core as a top-level module;
- Evidence Hub as a top-level module;
- separate Admin Console / Jobs;
- Developer Tools;
- Coordinate Quality as a top-level module;
- generic dashboards, readiness boards, workstream boards, blocker boards,
  activity timelines, and job dashboards.

Catalog Core/Data Dictionary remains an internal dependency for OTM table and
dependency validation.

## Created Boards On `Current Scope v2 - Prototype DNA`

| Board | Purpose |
|---|---|
| `00 / Current Scope + Visual System` | Scope lock, visual tokens, component grammar, and route summary. |
| `01 / Cockpit` | Context selector, project info, accelerator launcher, backend-owned launch state, and route recovery. |
| `02 / Master Data / Data Factory` | Data Factory, Template Builder, Quality Tools, stage rows, batch table, and Load Plan handoff. |
| `03 / Rates Studio` | Rate package hub, approval gate, validation stage rows, and artifact handoff. |
| `04 / Load Plan / Cutover` | Package intake, readiness, go/no-go gate, CSVUTIL/handoff stage rows. |
| `05 / Integration Mapping Studio` | Definition hub, mapping table, schema binding, preview/spec generation, and payload privacy note. |
| `06 / Order Release Generator` | Template start, order table, row editing, XML artifacts, and guarded submit readiness. |
| `07 / Assets Library` | Asset library, version/detail surface, guarded download, archive behavior, and Public View boundary. |
| `08 / Settings` | Projects/contexts, profiles/users/roles, settings table, access-policy review, audit save, and permission-denied state. |

## Applied Visual System

- IBM Plex Sans was available in Figma and used for the v2 boards.
- Compact desktop density was applied with fixed shell, top context bar,
  sidebar navigation, dense tables, chips, buttons, annotations, and stage rows.
- Accent color follows the complete mockup: `#2C5CC7`.
- The artifact remains low-fidelity: no decorative imagery, no high-fidelity
  interactions, and no expanded module scope.

## Validation

- Figma creation returned 9 boards on page `Current Scope v2 - Prototype DNA`.
- Screenshot checks were run for:
  - `00 / Current Scope + Visual System`;
  - `01 / Cockpit`;
  - `02 / Master Data / Data Factory`;
  - `05 / Integration Mapping Studio`;
  - `08 / Settings`.
- Follow-up fixes removed overlapped technical board titles from shell boards.
- Follow-up fixes expanded narrow stage rows so titles, descriptions, and
  action buttons do not overlap.

## 2026-05-27 Audit Pass

Michelangelo/Solon review compared the current wireframes against the module
wireframe briefs, active GUI specs, and the Complete Solution Mockup reference.

Applied Figma updates:

- added `09 UX Audit + Remediation Report`;
- added an audit strip to each active module board;
- corrected route labels from `/integration` to `/integration-mapping` and
  from `/order-release` to `/order-release-generator`.

Detailed report:

- `docs/agent/figma-wireframes/OTM_WORKBENCH_WIREFRAME_AUDIT_REPORT_2026_05_27.md`

## Design Guardrails

- No real client data is represented; synthetic context labels are used.
- Cockpit is not a project-management dashboard.
- Settings replaces separate Admin setup only for the current UI phase.
- Excluded modules require a new decision before returning to top-level
  navigation.
- Every implementation slice must still preserve client/domain, environment,
  and visibility/access-policy scope.
