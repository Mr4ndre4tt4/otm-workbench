# GUI Module Experience Roadmap

**Status:** active planning baseline
**Linear:** follows `OTM-108`
**Scope:** module-by-module GUI sequencing after the module experience architecture contract.

## 1. Purpose

This roadmap applies `GUI_MODULE_EXPERIENCE_ARCHITECTURE.md` to the current
OTM Workbench modules.

It defines the first useful GUI story for each module, the primary experience
pattern to use, and the main gaps that must be closed before a module is called
GUI-complete.

Module completion is governed by
`GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md`. This roadmap may mark first
functional slices as done, but a module is not complete until its full
module-specific authoring/configuration, artifact parity, negative QA,
out-of-order UI QA, security, and documentation evidence is complete.

## 2. Sequencing Rule

Do not start module GUI work by adding all available backend panels to one
screen.

For each module:

```text
1. Pick the primary object.
2. Pick the primary experience pattern.
3. Prove the workflow with backend-owned state.
4. Add operational surfaces only when they explain the workflow.
5. Record remaining gaps as Linear issues.
```

## 3. Current Completion Snapshot

| Module | GUI status | Backend status for first GUI story | Primary pattern | Current decision |
|---|---|---|---|---|
| Shell / Project Cockpit | Functional journey done | Platform context/preferences/navigation ready | Module overview | Keep hardening preferences/context. |
| Rates Studio | Functional journey done | Batch, validation, artifacts, approval ready | Object list/detail + operational surfaces | Treat as reference implementation. |
| Catalog Core | Functional journey done | Search/validation/macro APIs ready | Object list/detail | Good enough for current MVP0 slice. |
| Admin Console | Functional journey done | Setup, flags, jobs, audit ready | Tabbed detail + setup workflows | Keep advanced edit/delete for later. |
| Integration Mapping Studio | Functional journey done | Authoring, validation, preview/spec artifacts ready | Staged workflow | Closed for MVP0; harden later. |
| Load Plan / Cutover | First functional slice done | Backend flows mostly ready | Review queue + staged workflow | Continue with CSVUTIL, ZIP analysis, go/no-go, handoff commit, and artifact follow-ups. |
| Master Data / Data Factory | First functional slice done | Backend flows ready for seeded templates/batches | Staged workflow + object detail | Not complete; OTM-115 owns template factory, OTM CSV parity, durable state, and negative/out-of-order QA. |
| Coordinate Quality | No GUI journey | Backend/API ready | Staged workflow or review queue | Needs placement decision. |
| Assets Library | Partial GUI | Backend asset/version/link APIs ready | Object list/detail | Needs create/upload/link/download story. |
| Evidence Hub | First functional slice done | Evidence/artifact/archive APIs ready | Object list/detail + operational surfaces | Continue with archive history/detail only if needed. |
| Order Release Generator | Partial GUI | Template/batch/XML artifact APIs ready | Staged workflow | Good later candidate for end-to-end workflow. |

## 4. Recommended Next GUI Queue

### 4.1 Load Plan / Cutover

First GUI slice delivered because it connects planning, readiness, CSVUTIL,
artifacts, and handoff decisions across the backend-first roadmap.

```text
Primary object: package or checklist
Primary pattern: review queue + staged workflow
Delivered story: select package -> create checklist -> update item
evidence/status -> run checklist readiness -> inspect handoff eligibility.
```

Remaining GUI work:

```text
- Add CSVUTIL build UI from package/checklist.
- Add ZIP analysis and review queue decision UI.
- Add cutover package export and guarded artifact download.
- Add go/no-go commit workflow.
- Add handoff commit workflow after readiness export/archive evidence exists.
- Keep go/no-go, handoff eligibility, and artifact generation backend-owned.
```

### 4.2 Master Data / Data Factory

First GUI slice delivered after Load Plan. Data Factory now proves the staged
template/batch workflow pattern.

```text
Primary object: master data batch
Primary pattern: staged workflow + object detail
Delivered story: select template -> validate template -> build workbook ->
upload synthetic workbook -> validate relationships -> map -> build output ->
build CSV/export package.
```

Remaining GUI work:

```text
- Complete OTM-115 before calling the module complete.
- Implement OTM-116 backend dynamic template factory first, using
  docs/superpowers/specs/2026-05-22-master-data-dynamic-template-factory-design.md.
- Add UI-driven template authoring from N OTM tables.
- Add friendly labels, fixed/default values, and one-to-many field mappings.
- Add guarded workbook and CSV/ZIP downloads.
- Add Coordinate Quality placement and workflow.
- Add backend batch list/detail if durable batch return-state is required.
- Add guarded Load Plan registration from exported package.
- Add spreadsheet preview/editor only if it has a backend-owned use case.
- Add negative and out-of-order UI QA for human recovery paths.
- Keep OTM table/dependency validation backend-owned through Catalog Core.
```

### 4.3 Evidence Hub

First GUI slice delivered after Load Plan and Master Data produced richer
evidence/artifacts.

```text
Primary object: evidence item or archive package
Primary pattern: object list/detail + operational surfaces
First story: filter evidence -> inspect detail -> download guarded artifact ->
create archive package.
```

Remaining GUI work:

```text
- Add dedicated archive package history/detail screen if archives need to be
  browsed as first-class objects.
- Add deeper audit log exploration only when the backend exposes a focused
  Evidence Hub audit story.
```

### 4.4 Order Release Generator

Recommended after Data Factory patterns are stable because it is another
staged generator workflow.

```text
Primary object: order release generation batch
Primary pattern: staged workflow
First story: select template -> create batch -> preview XML -> generate XML
artifact -> show guarded OTM submit state.
```

Required GUI work:

```text
- Add batch authoring.
- Add XML preview surface as a documented exception if raw preview is needed.
- Add generated artifact list/download.
- Keep submit-to-OTM guarded by backend action contract.
```

### 4.5 Assets Library

Recommended when file/version management becomes necessary for module
collaboration.

```text
Primary object: asset
Primary pattern: object list/detail
First story: create asset -> upload version -> link to module object ->
download current version -> archive asset.
```

Required GUI work:

```text
- Add create/upload/link/archive actions.
- Use ArtifactList or version list for files.
- Keep file eligibility, version state, and links backend-owned.
```

## 5. Pattern Risks To Watch

```text
- Load Plan can become a long stacked page if checklist, package, readiness,
  export, and handoff are rendered as equal panels.
- Master Data can become confusing if template, workbook, batch, mapping, and
  CSV output are not staged.
- Evidence Hub can become a static catalog unless filters, archive action, and
  guarded downloads are part of the story.
- Order Release Generator can leak into raw XML tooling unless preview and
  submit actions are backend-controlled.
- Assets Library can drift into generic file manager behavior unless module
  links and version contracts stay central.
```

## 6. Cross-Module Requirements

All upcoming GUI module work must include:

```text
- backend-owned navigation and module visibility
- backend-owned actions or explicitly documented action gaps
- module completion status using First functional slice done / MVP workflow done
  / Module complete
- authoring/configuration surface when the module creates templates, mappings,
  packages, generators, or reusable definitions
- generated artifact parity checks against OTM/API target formats
- Data Dictionary and Oracle official/help documentation traceability when OTM
  behavior is ambiguous
- negative tests and out-of-order UI/browser QA
- functional QA journey with route return-state
- browser QA where possible
- no real client data
- no local artifact paths
- light/dark/system compatibility through tokens
- no module-specific visual identity
- Linear update with delivered scope and gaps
```

## 7. Immediate Recommendation

Next implementation target:

```text
Order Release Generator functional workflow
```

Reason:

```text
- Load Plan proved the review queue + staged workflow pattern.
- Master Data proved the template/batch staged workflow.
- Evidence Hub proved the shared artifact/evidence workspace.
- Order Release Generator is the next staged generator workflow already backed
  by template, batch, XML artifact, and submit-guard APIs.
```

Before coding, keep the first Order Release Generator GUI slice narrow: select
template, create batch, preview XML, generate XML artifact, inspect guarded OTM
submit state, route return-state.
