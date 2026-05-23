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
| Load Plan / Cutover | First functional slice plus CSVUTIL, ZIP review, sequence, exports, and Go/No-Go UI done | Backend flows mostly ready | Review queue + staged workflow | Continue with handoff commit and artifact download follow-ups. |
| Master Data / Data Factory | MVP workflow done | Backend flows ready for template authoring, batches, CSV/ZIP export, durable artifacts, and hardening QA | Staged workflow + object detail | Treat current workflow as MVP accepted; Coordinate Quality GUI, Load Plan registration, direct OTM import, and richer spreadsheet operations remain follow-ups. |
| Coordinate Quality | No GUI journey | Backend/API ready | Staged workflow or review queue | Needs placement decision. |
| Assets Library | Functional journey done | Backend asset/version/link/filter/classification APIs ready | Object list/detail + staged lifecycle workflow | Create/edit metadata, custom backend-owned classification authoring, system-protected classification guards, backend-owned available actions, structured metadata validation, Catalog/Data Dictionary metadata reference validation, selected-asset sync, guided module/macro-object/table/artifact/evidence link targets, Evidence Hub target filters, archived mutation guards, invalid OTM table, macro object, unsafe artifact, and unsafe evidence link recovery, and advanced filters are delivered; target pagination remains future scale follow-up only if needed. |
| Evidence Hub | First functional slice done | Evidence/artifact/archive APIs ready | Object list/detail + operational surfaces | Continue with archive history/detail only if needed. |
| Order Release Generator | First functional slice done | Template/batch/XML artifact/list/download APIs ready | Staged workflow | Guarded XML artifact download is delivered; richer row/template authoring and governed direct OTM submit remain follow-ups. |

## 4. Recommended Next GUI Queue

### 4.1 Load Plan / Cutover

First GUI slice delivered because it connects planning, readiness, CSVUTIL,
artifacts, and handoff decisions across the backend-first roadmap.

```text
Primary object: package or checklist
Primary pattern: review queue + staged workflow
Delivered story: select package -> create checklist -> update item
evidence/status -> run checklist readiness -> build CSVUTIL from checklist ->
inspect generated CTL/CL/manifest/evidence ids -> run ZIP analysis -> generate
review queue -> decide review items when present -> inspect handoff eligibility.
Then generate sequence snapshot, generate package readiness, export readiness
ZIP, export the cutover package from the checklist, and record Go/No-Go.
```

Remaining GUI work:

```text
- Add guarded artifact download.
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

Delivered after OTM-119:

```text
- UI-driven template authoring from Catalog/Data Dictionary-backed tables.
- Friendly labels plus fixed/default values and one-to-many target mappings.
- Template validation, workbook generation, workbook upload, relationship
  validation, mapping, output, CSV build, and CSV/ZIP export.
- Durable batch list/detail and batch-scoped artifact listing/download.
- Negative/out-of-order QA for missing artifacts, repeated CSV/export clicks,
  invalid upload recovery, and route leave/return recovery.
- Keep OTM table/dependency validation backend-owned through Catalog Core.
```

Remaining GUI work before `Module complete`:

```text
- Add Coordinate Quality placement and workflow.
- Add guarded Load Plan registration from exported package.
- Add direct OTM import only after submit/credential guardrails are designed.
- Add spreadsheet preview/editor only if it has a backend-owned use case.
- Expand advanced batch history filters/pagination if operational volume needs it.
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
- Guard generated artifact download through backend hash verification and audit
  logging.
- Keep submit-to-OTM guarded by backend action contract.
```

### 4.5 Assets Library

Recommended when file/version management becomes necessary for module
collaboration.

```text
Primary object: asset
Primary pattern: object list/detail
First story: library review with backend filters -> create asset -> upload
version -> link to module object or OTM table -> download current version ->
archive asset with lifecycle guards.
```

Required GUI work:

```text
- Add create/upload/link/archive actions.
- Add create-stage backend-owned classification authoring, with custom rows
  reused by the same metadata dropdowns and system-protected rows guarded by
  backend mutation rules.
- Add backend-owned create metadata fields for name, description, type,
  category, visibility, scope, sensitivity, module id, macro object, OTM table,
  and tags.
- Add structured backend validation details for invalid metadata
  classifications, including field, classification type, and allowed codes.
- Validate metadata `macro_object_code` against Catalog Core and
  `otm_table_name` against the OTM Data Dictionary before create/update.
- Add selected asset metadata update through the backend `PATCH` contract.
- Sync the authoring form from the selected backend asset before update.
- Preserve backend error codes/messages for invalid link targets, including Data
  Dictionary validation for `OTM_TABLE` and Catalog Core validation for
  `MACRO_OBJECT`.
- Add guided target selection from backend-owned platform navigation for
  `MODULE`, Catalog Core macro objects for `MACRO_OBJECT`, and Catalog Core
  Data Dictionary table search for `OTM_TABLE`.
- Add guided target selection from Evidence Hub client-safe evidence and
  artifact summaries for `EVIDENCE` and `ARTIFACT`.
- Add backend-owned Evidence Hub target filters for source module, evidence
  type, status, and artifact id before selecting `EVIDENCE` or `ARTIFACT`.
- Validate `ARTIFACT` and `EVIDENCE` links against Evidence Hub client-safe
  records in the backend before link creation.
- Add advanced backend-owned filters for scope, module id, macro object, and
  OTM table.
- Use ArtifactList or version list for files.
- Keep file eligibility, version state, and links backend-owned.
- Expose backend-owned `available_actions` for update, upload, link, download,
  and archive affordances.
- Reject archived asset metadata updates, version uploads, and link creation in
  backend mutation APIs.
- Keep the screen staged; do not return to stacked create/upload/link/list
  panels.
- Add pagination or virtualization only if artifact/evidence target lists become
  operationally large after backend filtering.
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
- backend-owned icon keys, module labels, program labels, and display metadata
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

Platform icon and label governance is tracked in
`GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md`. Until that platform slice is
implemented, Lucide icons may remain as temporary fallback renderers, but new
module work should avoid adding frontend-owned module identity maps.

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

First GUI functional slice is now implemented: select template, create batch,
preview XML, generate XML artifact, download the generated XML through the
backend artifact endpoint, inspect guarded OTM submit state, and return with
backend-owned recent batch state. Browser QA is covered by
`qa:functional:order-release:browser`. Next Order Release hardening should focus
on richer row/template authoring rather than direct OTM submit.
