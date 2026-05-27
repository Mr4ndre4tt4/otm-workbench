# Module Scope Ledger

**Status:** active recovery ledger
**Date:** 2026-05-27

## Purpose

This ledger recovers module intent before wireframes or code cleanup. It is the
working bridge between original foundation docs, consolidated GUI specs,
current implementation evidence, and the new governance process.

## Current UI Phase Filter

Only these modules are active top-level UI surfaces in the current To-Be
planning phase:

- Shell / Project Cockpit
- Master Data / Data Factory
- Rates Studio
- Load Plan / Cutover
- Integration Mapping Studio
- Order Release Generator
- Assets Library
- Settings

Catalog Core, Evidence Hub, separate Admin Console / Jobs, Developer Tools,
and Coordinate Quality as a standalone module remain documented, but are out
of the top-level UI for this phase.

## Scope States

```text
original
  Described by foundation docs, early specs, or Superpowers design docs.

implemented
  Present in current backend/frontend/tests/evidence.

validated
  Accepted as the target for the next redesign and delivery cycle.

to remove
  Candidate for cleanup after approval.

open
  Needs product decision or deeper review.
```

## Ledger

| Module | Original intent | Current validated scope | Cleanup watchlist |
|---|---|---|---|
| Shell / Project Cockpit | Give users a safe shell for authentication, active context, accelerator launch, Public View, and useful project references. | Active Figma target keeps one Cockpit screen with context selector, project info, and accelerator cards. It is not a project-management or readiness-control dashboard. | Readiness/workstream/blocker/activity/jobs dashboards in Cockpit, global action review surfaces, hidden post-sign-out navigation, private data mixed into Public View, secrets displayed without a security design. |
| Master Data / Data Factory | Prepare OTM master data using templates, batches, validation, conversion, CSV/ZIP, manifests, and evidence. | Hub with Data Factory, Template Builder, and Quality Tools. Operational batches and template authoring are separate route families. | Mixed stage strips that combine authoring, quality, upload, mapping, and output in one flow. |
| Catalog Core | Provide OTM Data Dictionary, macro-object, schema, reference, and dependency knowledge for modules. | Out of top-level UI for this phase. Remains a backend/internal validation source for OTM table, field, reference, and schema decisions. | Duplicate technical table explorers outside guarded internal contexts. |
| Rates Studio | Validate, approve, and export tariff/rate packages with evidence. | Batch lifecycle with validation, approval, CSV/XML/artifacts, evidence, and Load Plan handoff. | Single-page stacked panels, unbounded recent batch lists, approvals without route-level review. |
| Load Plan / Cutover | Consume packages, build CSVUTIL, analyze ZIPs, review setup, sequence loads, manage readiness and cutover handoff. | Route-level package/checklist/readiness/CSVUTIL/sequence/go-no-go/handoff journeys. | Treating Cutover as separate top-level module, long stacked pages, stale package switch state. |
| Evidence Hub | Canonical client-safe evidence and artifact audit. | Out of top-level UI for this phase. Evidence remains module-local or backend-traceable until reintroduced. | Raw payload display, filesystem paths, evidence views that rebuild source module logic. |
| Assets Library | Manage project assets, versions, links, classifications, and safe downloads. | Controlled asset lifecycle with backend-owned metadata, classifications, links, versions, and archive guards. | Generic file manager behavior, unvalidated links, mutations on archived assets. |
| Integration Mapping Studio | Author integration definitions, schema mappings, transformations, previews, specs, and artifacts. | Route-level definition hub, systems, schemas, mapping workspace, rule detail, review, preview, spec, artifacts. | One overloaded staged workspace, frontend-only suggestions, unclear alias/path blockers. |
| Order Release Generator | Generate OTM order release XML/artifacts from governed templates and row data. | Generator hub, template detail/builder/versioning, batch detail, row editor, XML preview, artifacts, guarded submit readiness. | Raw JSON editing, raw XML as the only preview, fake submit readiness. |
| Admin Console / Jobs | Manage users, roles, projects, profiles, environments, feature flags, jobs, audit, and governance. | Not a separate top-level UI module in this phase. Setup scope is absorbed into Settings; jobs stay out of the main UI. | Mixing setup into operational workflows, exposing sensitive configuration, reintroducing job dashboards without approval. |
| Developer Tools | Provide controlled technical diagnostics for DBA/MASTER/dev users. | Out of main UI for this phase. Guarded diagnostics remain restricted and hidden from normal workflows. | Public technical tools, local file paths, credentials, unsafe payloads. |
| Coordinate Quality | Validate Location coordinates and export correction/review artifacts. | Quality Tools route under Master Data with upload, persisted batch, result detail, export, and recovery. Not top-level navigation. | Treating coordinate validation as a Data Factory export step or standalone top-level module. |

## Validation Process Per Module

For each module:

1. read original foundation scope;
2. read current consolidated GUI spec;
3. read implementation/completion evidence;
4. record accepted target scope;
5. record to-remove candidates;
6. create Michelangelo wireframe brief;
7. create Figma wireframes for the active UI phase;
8. approve mockups;
9. create cleanup and implementation plan.

## Decision Gate

No module should enter cleanup or implementation until its ledger row is
reviewed and marked validated by the user.

## Validation Batches

### 2026-05-26 Phase 2A

Master Data / Data Factory:

- Scope review:
  `docs/agent/module-scope/MASTER_DATA_DATA_FACTORY_SCOPE_REVIEW.md`
- Wireframe brief:
  `docs/agent/wireframe-briefs/MASTER_DATA_DATA_FACTORY_WIREFRAME_BRIEF.md`
- Status:
  validated for wireframe brief; pending user approval before cleanup or
  implementation.

Catalog Core:

- Scope review:
  `docs/agent/module-scope/CATALOG_CORE_SCOPE_REVIEW.md`
- Wireframe brief:
  `docs/agent/wireframe-briefs/CATALOG_CORE_WIREFRAME_BRIEF.md`
- Status:
  validated for wireframe brief; pending user approval before cleanup or
  implementation.

### 2026-05-26 Phase 2B

The remaining module scope reviews and wireframe briefs were created:

- Shell / Project Cockpit
- Rates Studio
- Load Plan / Cutover
- Evidence Hub
- Assets Library
- Integration Mapping Studio
- Order Release Generator
- Admin Console / Jobs
- Developer Tools
- Coordinate Quality

Index:

- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`

Status:

- all modules are documented for user review;
- Shell / Project Cockpit v1 is superseded by the simplified v2 scope;
- no module is approved for cleanup or implementation by this documentation
  step alone.

### 2026-05-27 Complete Solution Mockup To-Be Consolidation

The active Complete Solution Mockup To-Be source keeps only:

- Cockpit
- Master Data / Data Factory
- Rates Studio
- Load Plan / Cutover
- Integration Mapping Studio
- Order Release Generator
- Assets Library
- Settings

Figma artifact:

```text
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
```

Status:

- active deep-flow boards created and validated in Figma;
- Settings absorbs project/profile/user/access setup for this phase;
- excluded modules require a new decision before returning to top-level UI;
- cleanup and implementation remain gated by user approval.
