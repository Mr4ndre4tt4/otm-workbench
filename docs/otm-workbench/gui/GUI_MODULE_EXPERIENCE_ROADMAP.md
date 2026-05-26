# GUI Module Experience Roadmap

**Status:** active planning baseline
**Linear:** follows `OTM-108`
**Scope:** module-by-module GUI sequencing after the module experience architecture contract.

See `GUI_MODULE_API_CONTRACT_MATRIX.md` for the backend API contract readiness
map across implemented GUI modules.

See `GUI_MODULE_ROADMAP_INDEX.md` for the module-by-module documentation index
that links each module to its most specific roadmap/spec/view/QA document.

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
| Shell / Project Cockpit | Functional journey done | Platform context/preferences/navigation ready | Module overview | Context draft feedback recovery is delivered; keep future shell work explicit and backend-owned. |
| Rates Studio | Functional journey done; list density first slice done; consolidated redesign spec drafted | Batch, validation, artifacts, approval ready | Object list/detail + operational surfaces, moving toward route-level lifecycle screens | `GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md` captures the consolidated objective, current MVP evidence, browser review findings, and next UX direction: hub, batch library, batch detail, staging, issues, CSV preview/export, approval, artifacts, evidence, and Load Plan handoff as route-level journeys. `OTM-143` caps noisy recent batches at 12 visible rows with long-label truncation. |
| Catalog Core | Functional journey done | Search/validation/macro APIs ready | Object list/detail | Good enough for current MVP0 slice; macro-object validation-result switch recovery is delivered. |
| Admin Console | Functional journey done; jobs density first slice done | Setup, flags, jobs, audit ready | Tabbed detail + setup workflows | Keep advanced edit/delete for later; selected-job feedback recovery is delivered. `OTM-143` caps noisy job rows at 10 visible rows with long-id truncation. |
| Integration Mapping Studio | Functional journey done; NDD-like executable positive, negative, required-target, backend-owned suggestion, first semantic suggestion, and next-action panel slices done | Authoring, validation, backend-owned mapping suggestions/scoring, all-or-nothing selected-suggestion bulk creation, Catalog-owned source/target path picking, mapping removal, required target checklist, spec/preview readiness, executable preview/spec artifacts ready | Staged workflow + next action | `OTM-152` proves mixed header + `Entregas[]` alias mappings and loop-scoped lookup through downloaded preview artifact content. `OTM-153` proves invalid alias/path blocker, blocked preview, backend-owned mapping removal, and correction without route reload. `OTM-154` proves backend-owned required target scenario-pack checklist. `OTM-159` moves mapping suggestions to backend contract with schema ownership validation and explicit UI load/apply. `OTM-160` adds exact, ambiguous, and first OTM-context scoring; the Rules UI now surfaces confidence/backend reason, can facet suggestions by backend-owned transform type, can pick official Catalog source and target paths, can select the currently visible suggestion subset into a local review set with source/target/transform/confidence/reason, create that selected review set through a backend-owned all-or-nothing bulk endpoint, clear it before apply, and clears selected suggestions after successful mapping creation. `OTM-161` extends the shared next-action panel to Integration Mapping from selected definition, payload/schema, mapping, validation, preview/spec, and artifact state. |
| Load Plan / Cutover | First functional slice plus CSVUTIL, ZIP review, sequence, exports, guarded downloads, Evidence Hub archive convenience, Go/No-Go, guarded handoff commit UI, next-action panel, out-of-order chaos slice, and consolidated redesign spec done | Backend flows mostly ready | Review queue + staged workflow + next action, moving toward route-level package lifecycle screens | `GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md` captures the objective, current MVP evidence, browser review findings, and next UX direction: hub, package library, package detail, checklist, readiness, CSVUTIL, ZIP review, sequence, exports, Go/No-Go, and handoff as route-level journeys. `OTM-146` proves package-switch cleanup for checklist, readiness, CSVUTIL, evidence draft, and stale feedback. |
| Master Data / Data Factory | OTM-115 completion acceptance met for MVP0; next-action panel first slice delivered; out-of-order chaos slice done | Backend flows ready for template authoring, backend-owned scenario packs, workbook editor contract/validation/batch creation, filtered/paginated batches, output/CSV preview, CSV/ZIP export, guarded direct OTM import readiness/submit refusal, durable artifacts, Load Plan package registration, cutover checklist creation/readiness with blocker display, Coordinate Quality preview/batches/results/export, date-column CSV alter-session parity, selected-template switch recovery, and hardening QA | Staged workflow + object detail + next action | Completion review captured in `GUI_MASTER_DATA_COMPLETION_REVIEW_OTM115.md`. `OTM-146` now proves template-switch cleanup through workbook, output, CSV, export, direct import guard, Load Plan handoff, and cutover checklist state; active-batch fallback is scoped to the selected template. Real governed direct OTM submission, deeper Load Plan analytics, advanced Coordinate Quality diagnostics, larger scenario library, and richer audited spreadsheet editing remain future scope. |
| Coordinate Quality | First functional slice done | Backend/API ready | Embedded Data Factory stage | Placement decision closed: keep inside `/master-data` as the Quality stage for Location coordinate preview, persisted batch, results, export, and return-state recovery. |
| Assets Library | Functional journey done; out-of-order chaos and list density slices done | Backend asset/version/link/filter/classification APIs ready | Object list/detail + staged lifecycle workflow | Create/edit metadata, custom backend-owned classification authoring, system-protected classification guards, backend-owned available actions, structured metadata validation, Catalog/Data Dictionary metadata reference validation, selected-asset sync, selected-asset switch recovery, guided module/macro-object/table/artifact/evidence link targets, Evidence Hub target filters, archived mutation guards, invalid OTM table, macro object, unsafe artifact, and unsafe evidence link recovery, and advanced filters are delivered. `OTM-146` now proves dirty metadata drafts, selected file upload state, and link target drafts are cleared when switching assets out of order; `OTM-143` caps noisy asset rows at 12 visible rows while preserving the selected asset; target pagination remains future scale follow-up only if needed. |
| Evidence Hub | Functional slice plus archive history and list density done | Evidence/artifact/archive APIs ready | Object list/detail + operational surfaces | Continue with archive detail/audit drill-down only if needed. `OTM-143` caps noisy evidence rows at 12 visible rows with long-label truncation. |
| Order Release Generator | First functional slice plus row, invalid-batch recovery, template authoring, template versioning, and out-of-order chaos hardening done | Template list/create/version, batch, XML artifact/list/download APIs ready | Staged workflow | Template-guided row editor replaced raw JSON input; invalid row issues now surface in the Batch stage and block Preview/Artifact actions until corrected; the Templates stage can create reusable backend-owned custom templates and new versions; template switching resets row drafts to the selected template defaults and clears active batch, stale preview, artifact, and submit guard state; governed direct OTM submit remains a guarded follow-up outside MVP0. |

## 4. Recommended Next GUI Queue

### 4.0 General QA Hardening Queue

The general solution QA on 2026-05-25 is recorded in
`GUI_GENERAL_SOLUTION_QA_2026_05_25.md`.

All browser functional module scripts and React functional tests passed in that
round, but the next roadmap items should target product usefulness, not only
test pass/fail:

```text
1. OTM-141: make browser QA reproducible with a backend-owned synthetic demo
   seed or documented local bootstrap command.
2. OTM-142/OTM-161: add a backend-owned next-action panel for staged modules.
   Data Factory, Load Plan, and Integration Mapping slices are delivered; keep
   future rollout tied to module-specific backend state or `available_actions`.
3. OTM-144: add grouped executable review for Integration Mapping so NDD-like
   mappings are understandable as an accelerator. First slice delivered in the
   Rules stage; multi-hop/aggregation execution remains `OTM-145`.
4. OTM-145: implement cross-collection/multi-hop joins, qualifier filters and
   aggregations in the Integration Mapping backend preview. First backend
   slice delivered for FILTER_BY_QUALIFIER and COUNT_DISTINCT.
5. OTM-147: add explicit multi-hop join-binding contract for Integration
   Mapping. First backend slice delivered with persisted bindings/hops and
   scalar preview provenance.
6. OTM-148: expose join-binding authoring and grouped review in the staged
   Integration Mapping Rules UI. Delivered with React and browser functional
   QA.
7. OTM-149: execute alias-scoped downstream mappings from join bindings.
   First backend slice delivered for scalar mappings with
   `transform_config.source_alias`.
8. OTM-150: execute loop-scoped alias mappings for Integration Mapping
   deliveries. Delivered for `$.deliveries[]` style target rows with
   source/target item provenance.
9. OTM-151: add semantic validation and UI assist for Integration alias
   mappings. Delivered missing/out-of-scope alias blockers plus an Alias source
   context selector in the mapping authoring form.
10. OTM-152: run the synthetic NDD-like browser scenario against executable
    preview artifacts. Delivered for mixed header + `Entregas[]` alias mappings
    and loop-scoped lookup output.
11. OTM-153: add negative browser QA for invalid alias/path recovery and
    blocked preview correction. Delivered with backend-owned mapping removal.
12. OTM-154: expose Integration Mapping required target scenario packs in
    backend validation, UI checklist, and browser QA. Delivered for the
    synthetic NDD-like checklist.
13. OTM-159: move Integration Mapping suggestions from frontend-local heuristic
    to backend-owned contract. Delivered with schema ownership validation,
    explicit Rules-stage load/apply action, React QA, and browser QA.
14. OTM-160: enrich Integration Mapping backend suggestion scoring with first
    Catalog/Data Dictionary-inspired semantics. Delivered exact match reasons,
    ambiguous exact-match downgrade, `StopSequence -> deliveries[].sequence`,
    and `ReleaseRefnumValue -> accessKey`.
15. OTM-146: add destructive/out-of-order browser journeys by module. First
    slices delivered with `npm run qa:chaos:browser` for Integration Mapping
    definition switching, Load Plan package switching, Master Data template
    switching, Assets Library asset switching, and Order Release template
    switching: dirty drafts, selected upload files, link target drafts,
    workbook/output/export/import/handoff state, checklist/readiness/CSVUTIL
    state, generated preview/submit guard state, and stale backend-owned
    suggestions are cleared when the selected backend object changes.
16. OTM-143: harden high-volume list density and signal quality. First slice
    delivered for Rates, Evidence Hub, Assets Library, and Admin jobs with
    shared row caps, selected-row pinning, truncation, and visible count
    summaries. Future work should use backend-owned presets/pagination when
    those contracts exist.
```

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
ZIP, export the cutover package from the checklist, download generated artifacts
through the guarded Evidence Hub endpoint, archive readiness export through
Evidence Hub, record Go/No-Go, and commit cutover handoff only when backend
eligibility is true.
```

Remaining GUI work:

```text
- Keep go/no-go, handoff eligibility, artifact generation, artifact downloads,
  Evidence Hub archive creation, and handoff commit backend-owned.
- Treat additional Load Plan GUI work as hardening or explicit new scope rather
  than missing MVP journey work.
```

### 4.2 Master Data / Data Factory

First GUI slice delivered after Load Plan. Data Factory proved backend coverage,
but product review found the single staged route confusing because it mixes
operational template consumption, template authoring, and Coordinate Quality.
The next implementation cycle should follow
`GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`.

OTM-115 owns template factory completion governance. The original backend-first
dynamic template design remains in
`docs/superpowers/specs/2026-05-22-master-data-dynamic-template-factory-design.md`.

```text
Primary object: master data batch
Primary pattern for next cycle:
Master Data hub -> operational Data Factory -> template detail -> batch detail,
with Template Builder and Quality Tools as separate route families.

Deprecated delivered story:
select template -> validate template -> build workbook or edit backend-owned
starter rows -> create/upload batch -> validate relationships -> map -> build
output -> build CSV/export package.
```

Delivered after OTM-119 and OTM-127:

```text
- UI-driven template authoring from Catalog/Data Dictionary-backed tables.
- Friendly labels plus fixed/default values and one-to-many target mappings.
- Template validation, workbook generation, workbook upload, relationship
  validation, mapping, output, CSV build, and CSV/ZIP export.
- Read-only backend-owned output record and generated CSV file previews.
- Durable batch list/detail and batch-scoped artifact listing/download.
- Backend-owned batch history filters for template, status, file name,
  minimum rows, page, and page size.
- Backend-owned batch history metrics for the current filters, including
  matching batches, matching rows, issues, and status count.
- Guarded Load Plan package registration from exported Master Data packages.
- Guarded cutover checklist creation from the registered Load Plan package.
- Guarded cutover checklist readiness generation from the created checklist.
- Read-only backend-returned readiness blocker display after checklist readiness.
- Negative/out-of-order QA for missing artifacts, repeated CSV/export clicks,
  invalid upload recovery, and route leave/return recovery.
- Backend-owned workbook editor contract, row validation, required-field
  recovery, and batch creation before upload.
- Guarded direct OTM import readiness and submit refusal after export, with
  backend-owned blockers for connection, credentials, and capability.
- Keep OTM table/dependency validation backend-owned through Catalog Core.
```

Required UX correction before further hardening:

```text
- Split `/master-data` into a hub with Data Factory, Template Builder, and
  Quality Tools entry points.
- Move template detail and batch execution into route-level detail pages with
  visible Back actions.
- Remove `Author`, `Map`, and `Quality` from the operational Data Factory
  workflow.
- Move authoring/mapping/version/publish actions into Template Builder.
- Add Template Builder search against backend-owned template header fields such
  as template code, client, type, macro object, status, version, tags, source
  basis, target OTM version, and description, with `begins with`, `contains`,
  `one of`, and `not one of` operators.
- Move template edit, copy, and delete/retire into dedicated route-level screens
  with visible Back actions and impact/state handling.
- Move Lat/Lon Validator into Quality Tools.
- Stop relying on the heavy selected-object side panel for core actions.
```

Remaining GUI work before `Module complete`:

```text
- Add deeper Load Plan export/handoff actions after checklist readiness only when
  they preserve the staged workflow.
- Add real direct OTM import only after submit/credential guardrails move from
  disabled readiness into governed connection, vault reference, allow-list,
  capability, audit, retry/job, and Oracle transport decisions.
- Add richer spreadsheet editing only if it extends the current backend-owned
  workbook editor with durable mutation/audit state.
- Add advanced Coordinate Quality map diagnostics and external provider setup
  only after backend provider governance is designed.
- Add deeper batch-history analytics beyond current-filter metrics only if
  operational volume needs it.
```

### 4.3 Evidence Hub

First GUI slice delivered after Load Plan and Master Data produced richer
evidence/artifacts.

```text
Primary object: evidence item or archive package
Primary pattern: object list/detail + operational surfaces
First story: filter evidence -> inspect detail -> download guarded artifact ->
create archive package -> review backend-owned archive history.
```

Remaining GUI work:

```text
- Add dedicated archive detail/audit drill-down only if archives need to be
  investigated as first-class objects.
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

Next implementation target after the current Integration Mapping hardening:

```text
Integration Mapping suggestion scoring and module review cleanup
```

Reason:

```text
- Integration Mapping now has backend-owned response handlers and guided
  CONSTANT, DATE_FORMAT, FILTER_BY_QUALIFIER, and COUNT_DISTINCT transform
  config authoring in addition to
  systems, endpoints, definitions, payloads, schema trees, mappings, loops,
  joins, join bindings, lookups, validation, required target packs, preview,
  spec generation, artifacts, and browser QA.
- The Rules stage now includes schema node search and deterministic first-pass
  mapping suggestions with visible confidence/backend reason, the first
  backend-owned `transform_type` facet, visible-subset selection plus clear
  recovery for a review set that displays source, target, transform, confidence,
  and reason, selected-suggestion cleanup after mapping creation, and governed
  all-or-nothing creation of selected suggestion sets through the backend.
  The next value gap is richer required-field semantics.
- Any next UI slice must keep the staged storytelling pattern and grouped review
  as the central workspace.
```

Order Release Generator first GUI functional slice remains implemented:
create/select template, create batch, preview XML, generate XML artifact,
download through the backend artifact endpoint, inspect guarded OTM submit
state, and return with backend-owned recent batch state. Browser QA is covered
by `qa:functional:order-release:browser`; direct OTM submit remains intentionally
guarded until connection, credential, audit, and capability governance are
designed.
