# OTM Workbench Wireframe Audit Report

**Status:** supporting historical Figma remediation report
**Date:** 2026-05-27
**Figma file:** `OTM Workbench - Consolidated Scope Wireframes`
**File key:** `zJGLRJCTArRStISGIPQ2DQ`
**Audited page:** `Consolidated UI Scope Wireframes`

## Supersession Notice

This report documents gaps from the earlier consolidated wireframe pass. The
active To-Be source is now the Complete Solution Mockup deep-flow board set:

```text
OTM Workbench - Complete Solution Mockup
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
```

The deep-flow boards address the main route-depth and action-mapping gaps
identified here. Keep this report as supporting audit evidence.

## Inputs Reviewed

- Active Figma wireframe boards:
  - `00 Scope Map - UI Phase`
  - `01 Cockpit`
  - `02 Master Data / Data Factory`
  - `03 Rates Studio`
  - `04 Load Plan / Cutover`
  - `05 Integration Mapping Studio`
  - `06 Order Release Generator`
  - `07 Assets Library`
  - `08 Settings`
- Reference Figma mockup: `OTM Workbench - Complete Solution Mockup`
  (`7AkORIWrjmaOiBBA6cMOj9`)
- Current Solon scope and module wireframe briefs under `docs/agent/`.
- Current GUI specs under `docs/otm-workbench/gui/`.

## Executive Summary

The current Figma wireframe is directionally aligned with the approved
eight-module UI phase and the reference mockup's compact workbench visual DNA.
It correctly excludes Catalog Core, Evidence Hub, separate Admin/Jobs,
Developer Tools, standalone Coordinate Quality, and generic dashboards from
top-level navigation.

The main gap is depth: most modules are represented as one macro board, while
the specs require route-level screens, deliberate modals, blocked states, and
recovery paths. Several visible labels behave like actions but do not yet map
to a destination screen or dialog.

## System-Level Findings

| ID | Severity | Finding | Required update |
|---|---|---|---|
| WF-AUD-01 | P1 High | Most modules compress multiple required route families into one board. | Add route coverage frames or explicit route strips for every required child screen. |
| WF-AUD-02 | P1 High | Action-like labels such as `open`, `Create batch`, `validate`, `edit`, `preview XML`, `review`, `handoff`, and guarded download do not all show target screens. | Map each action to a route, modal, blocked state, or explicit no-op note. |
| WF-AUD-03 | P1 High | Critical confirmations are missing or only described in text. | Add deliberate modal/review frames for approval, export, go/no-go, handoff, archive, privilege changes, and secure-vault reveal. |
| WF-AUD-04 | P2 Medium | Some implementation notes are useful for review but noisy for final operator screens. | Keep these in audit strips/report boards, then remove or convert them to implementation annotations before approval. |
| WF-AUD-05 | P2 Medium | Two route labels diverged from specs. | Corrected in Figma: `/integration-mapping` and `/order-release-generator`. |

## Module Findings

### Cockpit

**Coverage:** partial.

Current board covers `/home`, context selector, project info, accelerator
launcher, and no-project-management guardrail.

Missing or loose:

- `/login`;
- `/logout` or session-ended state;
- expanded context selector;
- no active context blocked state;
- user-menu popover;
- Light/Dark toggle behavior;
- secure-vault reveal dialog placeholder;
- explicit route destinations for each accelerator `open` action.

### Master Data / Data Factory

**Coverage:** partial.

Current board shows hub, Template Builder summary, batch table, validation
detail, CSV rule, and Quality Tools separation.

Missing or loose:

- `/master-data/factory`;
- template detail and upload intent;
- route-level batch execution detail;
- Template Builder list, new, detail, edit, copy, delete/retire;
- Quality Tools hub;
- Lat/Lon validator and batch result;
- export complete and Load Plan registration state;
- disabled action reasons before CSV/export actions.

### Rates Studio

**Coverage:** partial.

Current board shows rates hub, rate package detail, table rows, and one review
card.

Missing or loose:

- batch creation route;
- staged table detail;
- issues route;
- CSV preview route;
- export review;
- approval review;
- artifacts/evidence routes;
- Load Plan handoff route;
- blocked approval/export states with backend reasons.

### Load Plan / Cutover

**Coverage:** partial.

Current board shows package review, go/no-go gate, dependency table, and
handoff summary.

Missing or loose:

- package detail route index;
- checklist;
- readiness;
- CSVUTIL;
- ZIP review;
- sequence;
- exports;
- dedicated go/no-go review;
- dedicated handoff confirmation with eligibility and evidence.

### Integration Mapping Studio

**Coverage:** partial.

Current board shows definition hub, mapping workspace, mapping table, preview
and spec summary, and privacy note.

Figma update applied:

- route labels changed from `/integration` to `/integration-mapping`.

Missing or loose:

- definition create/detail routes;
- systems route;
- schema binding;
- mapping route;
- rule detail;
- rules list;
- review route;
- preview blocked/generated states;
- spec and artifact routes;
- invalid alias/path state.

### Order Release Generator

**Coverage:** partial.

Current board shows template-guided start, order workspace, order table,
guarded submit, and artifact note.

Figma update applied:

- route labels changed from `/order-release` to
  `/order-release-generator`.

Missing or loose:

- template new/detail/version screens;
- batch new/detail;
- row editor route;
- XML preview route;
- artifacts route;
- submit-readiness route;
- invalid row state;
- preview blocked state;
- submit not-implemented/governed state.

### Assets Library

**Coverage:** partial.

Current board shows asset library hub, asset detail, asset table, guarded
download, and not-a-file-manager note.

Missing or loose:

- new asset route;
- edit route;
- versions and new-version routes;
- links route;
- classification list/new/edit;
- archive impact review;
- invalid link target;
- archived asset mutation blocked;
- protected system classification state.

### Settings

**Coverage:** partial.

Current board correctly absorbs setup/admin scope into Settings and keeps Jobs
and Developer Tools out of top-level UI.

Missing or loose:

- project/context detail and edit flows;
- profile/user/role/grant flows;
- access-policy review;
- privilege-change confirmation;
- permission denied state;
- audit save feedback;
- explicit no separate Jobs/Dev Tools entry.

## Figma Updates Applied

- Added board `09 UX Audit + Remediation Report`.
- Added an audit strip to each active module board.
- Corrected route labels:
  - `/integration` -> `/integration-mapping`;
  - `/order-release` -> `/order-release-generator`.

## Approval Gate

Do not approve implementation cleanup from the current boards until:

- every visible action maps to a route, deliberate modal, blocked state, or
  explicit no-op note;
- every critical operation has a review/confirmation surface;
- every module's required empty, blocked, validation, permission, and recovery
  states are represented;
- out-of-scope modules remain absent from sidebar, Cockpit launchers, and
  active route mockups.
