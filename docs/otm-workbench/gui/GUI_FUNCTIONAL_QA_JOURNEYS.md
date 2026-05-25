# GUI Functional QA Journeys

**Status:** active baseline
**Date:** 2026-05-21
**Scope:** functional UI journeys, state transitions, and backend contract validation.

## 1. Purpose

The visual QA matrix proves that screens render consistently. This document
defines what each screen must be able to do.

Functional GUI QA must prove that a user can enter a route, perform the
screen's primary workflow, navigate away, return, and still see backend-owned
state reflected correctly. The frontend may orchestrate the workflow, but
validation, permissions, lifecycle, jobs, artifacts, evidence, and generated
files stay backend-owned.

`GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md` defines the higher bar for
calling a module complete. A route journey marked DONE in this document proves a
workflow slice; it does not by itself prove module completion.

## 2. Test Layers

Functional GUI QA uses three layers.

```text
Layer 1: frontend contract tests
- Vitest + Testing Library.
- Mock backend responses.
- Prove UI behavior, routing, disabled states, action wiring, and API calls.

Layer 2: browser journey tests
- Playwright or accepted browser fallback against local FastAPI + Vite.
- Synthetic SQLite database.
- Prove login, navigation, real HTTP contracts, state transitions, and return
  navigation.

Layer 3: backend functional confirmation
- Focused pytest flows using FastAPI TestClient.
- Prove the backend state transitions that the UI journey depends on.
```

No journey is considered complete until the UI assertion and the backend state
assertion agree.

## 3. Required Journey Pattern

Every functional route should eventually have a journey with this shape:

```text
1. Start from login or persisted authenticated session.
2. Open the module through backend-owned navigation.
3. Confirm the route loads with expected empty or seeded state.
4. Execute the primary action.
5. Confirm the relevant API was called with bearer auth.
6. Confirm the UI shows success, blocked, or error state from backend response.
7. Navigate to another route.
8. Return to the original route.
9. Confirm backend-owned state is still visible.
10. Confirm no console errors and no real client data in visible text.
```

For destructive, external, or file-producing actions, the journey also confirms
confirmation UX, audit/evidence output, and client-safe artifact metadata.

For module completion, the journey set must also cover:

```text
- invalid inputs and invalid lifecycle order
- repeated clicks or duplicate submit attempts
- changing selected object/template mid-flow
- clearing or replacing uploaded files
- navigation away/back at intermediate stages
- backend error or blocked-state recovery
- generated artifact content parity
```

## 4. Coverage States

Use these values in the route matrix.

```text
DONE       implemented and validated in this repo
PARTIAL    some coverage exists, but not the full functional journey
TODO       no dedicated functional journey yet
BLOCKED    waiting for backend contract, UI surface, or test harness
```

These coverage states are route journey states, not module completion states.
Use `First functional slice done`, `MVP workflow done`, and `Module complete`
from `GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md` for module-level status.

## 5. Route Journey Matrix

| Route | Owner issue | Primary functional journey | Layer 1 UI contract | Layer 2 browser journey | Layer 3 backend confirmation | Return-state check | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` and `/home` | OTM-101 | Attempt invalid login, edit the login draft without keeping stale auth feedback, log in, load cockpit, apply active context, edit the context draft without keeping stale submit feedback, refresh readiness, update preferences, navigate away and return. | DONE: `AppFunctionalShell.test.tsx` plus `LoginPanel.test.tsx`, `ContextSwitcher.test.tsx`, `PreferenceControls.test.tsx`, and `WorkbenchShell.test.tsx`; login/context draft changes clear stale feedback, preference clicks keep backend-owned persistence, topbar/sidebar preference failures render shared inline backend error feedback, and `FeedbackMessage` announces short success/error feedback through status/alert roles. | DONE: `npm run qa:functional:shell:browser` covers failed-login recovery, context apply, domain draft recovery, preference updates, navigation, and return-state. | DONE: `test_gui_shell_backend_contracts.py` covers login/session, backend navigation icon/label metadata, active context, persisted preferences, cockpit summary, capabilities, and unauthenticated shell read guards. | Context and preferences remain visible after leaving and returning; login and context draft-level feedback does not survive changed drafts. | None for the current shell foundation journey; future preference work should be explicit new scope. |
| `/rates` | OTM-102 | Create/import batch, add tables, validate, inspect issues, approve when ready, preview/export CSV, download artifact, switch batches with a clean CSV/export workspace. | DONE: dedicated `AppFunctionalRates.test.tsx` covers create batch, add table row, CSV preview, CSV export, artifact download, approval confirmation with approval note, approval evidence display, evidence display, blocker display, validate action surface, and batch-switch recovery with stale preview/download feedback cleared. | DONE: `npm run qa:functional:rates:browser` covers create batch, stage ACCESSORIAL_COST, preview CSV, export ZIP, download artifact, switch to an alternate batch with preview/export/download state cleared, switch back, approve with confirmation note, approval evidence, leave route, and return-state assertion against local FastAPI + Vite. | DONE: rates batch, validation, approval, CSV preview/export, artifacts/evidence backend tests exist. | Created/selected batch, staged table rows, exported artifacts, approval evidence, and selected batch state remain visible after navigation; CSV preview/download feedback is batch-workspace scoped and clears when selecting another batch. | None for the current Rates MVP0 functional slice. |
| `/catalog` | OTM-90 | Search table/column/reference, validate input, inspect macro object dependencies and load plan. | DONE: `AppFunctionalCatalog.test.tsx` covers macro detail/tables/load plan plus table, column, and reference validation API calls/results, then macro-object switch recovery with stale validation results cleared and reset recovery back to default synthetic validation fields. | DONE: `npm run qa:functional:catalog:browser` covers Catalog navigation, explicit RATE_RECORD selection, table/load-plan inspection, table validation, column validation, reference validation, macro-object switch recovery, validation reset recovery, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: `test_catalog_core.py`. | Last selected macro/table can be reselected and still matches backend response; validation form can return to a known baseline without route reload and clears route-session validation results when the selected macro object changes. | Reference option browser remains future enhancement; current validation journey is covered. |
| `/master-data` | OTM-114 | Follow the staged Data Factory workflow: select template, author/reset a template draft, validate template, build workbook or edit backend-owned rows, create/upload a batch, validate relationships, map records, build output, inspect backend-owned output preview, build CSV, inspect CSV preview, export package, verify guarded direct OTM import readiness, register exported package for Load Plan, create cutover checklist, generate checklist readiness, inspect readiness blockers, filter durable batch history, leave route, and return with backend-owned template state visible. | DONE: `AppFunctionalMasterData.test.tsx` covers staged workflow navigation, template authoring, backend-owned scenario pack selection, scenario story display, scenario draft creation from server-owned payload, authoring-draft reset recovery with stale feedback/result panels cleared, template validation, workbook editor contract fetch, edited-row required-field validation failure/recovery, editor batch creation, workbook generation, FormData upload, invalid upload recovery, relationship validation, map, output preview, CSV preview, export, guarded direct OTM import readiness, blocked submit error surfacing, Load Plan package registration, cutover checklist creation/readiness, readiness blocker display, backend batch history filters including file name and minimum rows, backend batch history metrics, durable batch inspection/recovery, active-row `aria-current`, bearer-auth API assertions, and route return-state. | DONE: `npm run qa:functional:master-data:browser` covers login, Data Factory navigation, backend-owned Location operational and Item Packaging scenario pack selection, scenario story display, manual authoring controls hidden while each pack is active, scenario draft creation/validation/publish/reset recovery, Author-stage synthetic draft creation/publish/reset recovery, explicit `REGIONS_BASIC` selection, template validation, workbook generation, backend-owned workbook editor required-field failure/recovery, editor batch creation, relationship validation, map, output preview, CSV preview, export package, guarded direct OTM import readiness/blocked submit, Load Plan package registration, cutover checklist creation/readiness with backend blocker display, backend batch filters and reset recovery, active durable batch row `aria-current`, route return to Output, durable batch/artifact visibility, console health, and HTTP health against local FastAPI + Vite. | DONE: `test_master_data_templates.py` covers template validation, workbook generation, upload parsing, workbook editor contract, editor row validation, editor batch creation, relationship validation, mapping, output records, output record listing, CSV files, CSV preview listing, filtered/paginated batch listing with file-name and minimum-row filters, filtered batch-history summary metrics, export package, artifacts, evidence, manifest behavior, idempotent CSV/export retries, and the first operational scenario pack: Location with address/capacity/activity time/dock/equipment restriction tables plus Item/Ship Unit Spec/Packaged Item/TiHi. `test_master_data_direct_otm_import_guard.py` covers guarded direct OTM import readiness, missing export, exported package guard blockers, blocked submit, audit safety, and no job creation. `test_load_plan_package_intake.py` covers Master Data package intake, idempotency, evidence, audit, and event creation; Load Plan checklist tests cover checklist creation and readiness from package. | Template state and durable batch/artifact rows remain visible after leaving and returning through backend list endpoints; authoring draft state can return to a synthetic baseline without route reload; selecting another template or batch clears route-session workbook, upload, output/export, guarded import, Load Plan handoff, checklist, and stale feedback state. | Real direct OTM import, deeper spreadsheet editing, deeper Load Plan export/handoff, and deeper batch-history analytics remain follow-up scope. |
| `/master-data` coordinate quality | OTM-91 | Validate Location lat/lon preview, create batch, inspect results, export correction/review package. | DONE: `AppFunctionalCoordinateQuality.test.tsx` covers the embedded Quality stage, preview, batch create, results, export package, bearer-auth API assertions, and route return-state. | DONE: `npm run qa:functional:coordinate-quality:browser` covers login, Data Factory navigation, Quality stage preview, persisted batch, export package, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: coordinate quality API and engine tests exist, including batch listing, results, and export. | Recent batch and result counts persist after returning through backend list/result endpoints. | Advanced map diagnostics, external provider configuration, and deeper negative/out-of-order QA remain follow-up scope. |
| `/load-plan` | OTM-109 | Select an upstream-registered package, create the cutover checklist, link evidence while marking one checklist item CSVUTIL-ready, reset the checklist evidence draft, generate checklist readiness, build CSVUTIL CTL/CL artifacts from the checklist, download a guarded CSVUTIL artifact, run ZIP analysis, generate/decide review queue items, generate sequence snapshot, generate package readiness, export readiness ZIP, export cutover package, download a guarded export artifact, archive readiness export through Evidence Hub, inspect handoff eligibility blockers, record Go/No-Go, commit cutover handoff when eligible, switch to another package with a clean route-session workspace, leave the route, and return with package state still visible. | DONE: `AppFunctionalLoadPlan.test.tsx` covers staged workflow navigation, checklist creation, item PATCH with bearer auth/evidence and `method=CSVUTIL`, checklist evidence draft reset recovery with stale feedback cleared, readiness generation, CSVUTIL build-from-checklist POST with bearer auth/default parameters, guarded Evidence Hub download for CSVUTIL and export artifacts, Evidence Hub archive package creation for readiness export evidence, ZIP analysis POST, review queue generation/listing, review item decision POST, sequence snapshot POST/blockers, package readiness generation, readiness export, cutover package export, Go/No-Go POST/decision evidence, artifact/finding/status display, handoff eligibility blockers, guarded handoff commit POST when eligible, package-switch recovery with stale feedback/Go-No-Go/handoff state cleared, and route return-state. | DONE: `npm run qa:functional:load-plan:browser` seeds two synthetic Rates packages through backend APIs, opens Load Plan, creates checklist, updates one item with client-safe evidence as CSVUTIL-ready, resets checklist evidence draft, generates readiness, builds CSVUTIL, verifies CTL/CL/manifest/evidence ids, downloads a CSVUTIL artifact through Evidence Hub, runs ZIP analysis, generates clean review queue, generates sequence snapshot, generates package readiness, exports readiness and cutover package artifacts, downloads and archives a readiness export artifact through Evidence Hub, inspects handoff eligibility blockers, verifies handoff commit remains disabled while blocked, records Go/No-Go, switches to the other package and verifies stale Go/No-Go state is gone, and verifies return-state against local FastAPI + Vite. | DONE: Load Plan/Cutover/CSVUTIL/ZIP analysis/review queue/sequence/readiness export/cutover package/Go-No-Go/handoff backend tests cover major flows; Evidence Hub artifact download/archive backend tests cover guarded download, archive evidence, audit, and hash/path safety. | Registered package remains visible after leaving and returning; checklist/readiness/CSVUTIL/ZIP review/sequence/export/download/archive/Go-No-Go/handoff commit actions are backend-owned; evidence draft and package route-session state can return to a known baseline without route reload. | None for the current Load Plan MVP GUI journey; further work should be hardening or explicit new scope. |
| `/assets` | OTM-93 | Follow the staged lifecycle: review library with backend filters, author a custom backend-owned classification, author and edit asset metadata, switch selected assets, upload version, recover from invalid OTM table and macro object link validation, link to module object, OTM table, Catalog Core macro object, Evidence Hub artifact, or Evidence Hub evidence, download current version, archive asset, verify archived update/upload/link guards, switch to another asset with a clean route-session workspace, leave the route, and return with backend state visible. | DONE: `AppFunctionalAssets.test.tsx` covers staged workflow navigation, backend classification filters plus advanced scope/module/macro-object/OTM-table filters and reset recovery, create-stage custom classification authoring and immediate dropdown reuse, metadata-driven create and update payloads, selected-asset form synchronization, selected-asset switch recovery with stale archive feedback cleared, version upload, guided `MODULE`/`MACRO_OBJECT`/`OTM_TABLE`/`ARTIFACT`/`EVIDENCE` target selection from backend contracts, Evidence Hub target filters and reset recovery, invalid `OTM_TABLE` and `MACRO_OBJECT` validation with backend error codes, selected link type/target payloads, guarded current-version download, archive, backend-owned available action disabled states, bearer-auth assertions, and route return-state through backend list/detail. | DONE: `npm run qa:functional:assets:browser` covers login, context setup, backend filter controls including scope/module/macro-object/OTM-table filters and reset recovery, staged asset metadata authoring/editing, version upload, invalid OTM table and macro object recovery, guided OTM table, macro-object, artifact, and evidence target selection, Evidence Hub target filter reset recovery, OTM table, macro object, artifact, and evidence link creation, current-version download, archive, archived upload/link disabled states, selected-asset switch recovery to a non-archived asset, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: assets backend tests cover foundation, create/update/archive, custom classification create/update with system-protected mutation guard, available_actions, archived update/upload/link mutation guards, structured metadata validation details, Catalog/Data Dictionary metadata reference validation, permissions, links, versions, download audit, filter contracts, Data Dictionary table search/link validation, Catalog Core macro-object link validation, Evidence Hub artifact/evidence client-safe link validation, and secret-risk guards. | Archived/versioned state is preserved and visible after returning through backend-owned list/detail/version/link endpoints; route-session archive/download/link feedback clears when the selected backend asset changes. | Target list pagination/virtualization remains future scope only if Evidence Hub volumes require it. |
| `/evidence` | OTM-94 | Filter evidence, inspect detail, download guarded artifact, create archive package, review backend-owned archive history, switch selected evidence with clean operation feedback, leave route, and return with backend-owned evidence visible. | DONE: `AppFunctionalEvidenceHub.test.tsx` covers filters, reset recovery, detail, guarded download, archive package creation, backend-owned archive history, evidence-selection recovery with stale archive feedback cleared, bearer-auth API assertions, and route return-state. | DONE: `npm run qa:functional:evidence:browser` seeds synthetic backend evidence, filters, resets filters back to the unfiltered backend list, reapplies filters, downloads artifact, creates archive, validates backend-owned archive history, switches selected evidence and validates stale archive feedback is cleared, and validates return-state against local FastAPI + Vite. | DONE: `test_evidence_hub_index.py` covers list/detail, filters, guarded artifact download, archive package creation, audit/event records, and safe metadata. | Filtered evidence remains visible after leaving and returning. Latest archive package is visible during the route session; archive history remains backend-list-driven through evidence records; selected-evidence operation feedback clears when selection changes. | Archive detail/audit drill-down remains future scope only if archives need richer investigation. |
| `/order-release-generator` | OTM-95, OTM-125 | Create a reusable backend-owned template, create a new template version, select template/version, author batch rows from template-guided fields, reset rows from selected template defaults, create batch, inspect invalid row issues when present, correct rows, preview XML, generate XML artifact, download XML through the guarded backend artifact endpoint, verify guarded OTM submit state, switch templates and recover to a clean batch workspace. | DONE: `AppFunctionalOrderReleaseGenerator.test.tsx` covers backend-owned custom template creation from the Templates stage, backend-owned template version creation, template selection, template-guided row editor, reset-row recovery from template defaults, template-switch recovery with stale batch/preview/artifact/submit state cleared, edited row payload, backend batch creation, invalid row issue display, invalid batch Preview/Artifact blocking, corrected-row recreate, XML preview, XML artifact generation, artifact list/download URL, guarded download call, submit guard, bearer-auth assertions, and route return-state through backend batch list. | DONE: `npm run qa:functional:order-release:browser` covers login, context setup, custom alternate template creation, template selection, row reset recovery, batch creation, XML preview, XML artifact generation, guarded artifact download, guarded submit, template-switch recovery, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: OR generator backend tests cover template list/create/version validation, template version schema migration, batches, batch listing, preview, XML artifact, artifact list/download with hash verification and audit, cross-batch artifact rejection, submit guard, jobs, evidence, and client-safe synthetic data. | Recent batch state remains visible after leaving and returning through backend-owned `/batches` list. Created templates and versions are backend-owned and reloaded through `/templates`. Preview/artifact/download/submit guard state is route-session scoped and cleared when the selected backend template changes. | Direct OTM submit remains guarded/out of MVP0. |
| `/integration-mapping` | OTM-96 | Follow the staged workflow: systems/endpoints, definition, payloads/schemas, mapping rules, definitions list. Create source/target payloads, parse schema documents, create mapping, loop, join, and lookup rules from schema node selectors, reset mapping-rule drafts, validate, preview, generate spec, list generated artifacts, download the generated spec, switch to another definition with a clean definition workspace, leave and return with backend-owned definition still visible. | DONE: `AppFunctionalIntegrationMapping.test.tsx` covers staged navigation, system/endpoint creation, definition creation, manual payload/schema creation, schema node path picking for mapping/loop/join/lookup, mapping/loop/join/lookup payload/auth assertions, mapping-rule draft reset recovery with stale feedback cleared, validate, preview, spec generation, generated artifact listing/download, definition-switch recovery with stale feedback cleared and mapping schema drafts reset, and return-state check. | DONE: `npm run qa:functional:integration-mapping:browser` covers login, Integration Mapping navigation, staged workflow navigation, real system/endpoint/definition/manual payload/schema creation, schema node path picking, mapping/loop/join/lookup creation, mapping-rule draft reset recovery, validate, preview, spec generation, artifact download, two-definition switch recovery with stale artifact feedback cleared, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: integration mapping backend tests cover systems/endpoints, definitions, payloads, schema persistence/tree, mappings, loops, joins, lookups, validation, preview, spec, generated artifacts/download, audit, and synthetic E2E. | Created system/endpoint, definition, manual payload schemas, mapping, loop, join, lookup, and generated artifact metadata remain visible after leaving and returning; rule draft fields and definition-scoped feedback can return to a clean baseline without route reload. | None for the current Integration Mapping MVP0 functional slice. |
| `/admin` or setup surfaces | OTM-97 | Review current admin user, author workspace/project/profile/environment setup, reset setup drafts, inspect capabilities, feature flags, jobs, and audit logs; enable `dev_tools`; create a synthetic `DEMO_ECHO` job; inspect events; cancel a pending job; create/run a second job; leave and return with backend-owned job state still visible. | DONE: `AppFunctionalAdmin.test.tsx` covers setup authoring, setup draft reset recovery with stale feedback cleared, setup/capability/feature-flag/audit panels, feature flag update, demo job creation, job event detail, cancel action, run action, job-selection recovery with stale operation feedback cleared, API payload/auth assertions, and return-state check. | DONE: `npm run qa:functional:admin:browser` covers login, context seed, Admin navigation, workspace/project/profile/environment authoring, setup draft reset recovery, setup/capability/audit visibility, feature flag enable, demo job create/cancel/events, demo job create/run/events, job-selection recovery with stale completion feedback cleared, route return, console health, and HTTP health against local FastAPI + Vite. | DONE: `test_operational_metadata.py`, `test_operational_context.py`, and cockpit setup tests cover feature flags, jobs, audit, and setup contracts. | Authored setup entities, enabled feature flag, plus cancelled and succeeded job statuses remain visible after navigation; setup draft fields can return to a clean baseline without route reload; selected-job operation feedback clears when the selected job changes. | Advanced edit/delete/pagination UX remains future scope. |

## 6. Backend Contracts By Route

```text
/ and /home:
  session login, navigation, user-preferences, projects, profiles,
  environments, active-context, project-cockpit summary.

/rates:
  Rates templates, batches, batch detail, tables, validate, issues, readiness,
  approve, csv-preview, export-csv, artifacts, latest export, evidence,
  downloads, Catalog/reference helpers.

/catalog:
  Catalog table, columns, reference options, macro objects, load-plan, validate
  table, validate column, validate reference.

/master-data:
  Master Data templates, validate, build-workbook, batches,
  filtered/paginated batches, validate-relationships, map, build-output,
  output-records, build-csv, csv-files, export-csv-package, Load Plan package
  registration from exported batch, cutover checklist creation from package,
  cutover checklist readiness and blocker display,
  Coordinate Quality validate/batches/results/export.

/load-plan:
  packages, summary, cutover checklist templates/detail/item patch/readiness,
  export package, go-no-go, sequence, cutover readiness, handoff, CSVUTIL,
  ZIP analysis, review queue, guarded Evidence Hub artifact download, cutover
  handoff commit.

/assets:
  classifications, custom classification create/patch, create/list/detail/patch/archive, links, download, versions.

/evidence:
  evidence list/detail, archive packages, artifact download, platform audit
  and evidence metadata.

/order-release-generator:
  templates list/create/version, batches, preview-xml, generate-xml-artifact, artifact list/download, submit guard.

/integration-mapping:
  transform types, definitions, systems/endpoints, payload artifacts, schema
  tree/documents/nodes, mappings, loops, joins, lookups, validate, preview,
  generate-spec, generated artifacts, guarded artifact download.

/admin or setup:
  workspaces, projects, profiles, environments, capabilities, feature flags,
  jobs, job events, audit logs.
```

## 7. Script Targets

Current implemented scripts:

```text
npm run qa:functional
npm run qa:functional:admin
npm run qa:functional:admin:browser
npm run qa:functional:assets
npm run qa:functional:assets:browser
npm run qa:functional:catalog
npm run qa:functional:catalog:browser
npm run qa:functional:coordinate-quality
npm run qa:functional:coordinate-quality:browser
npm run qa:functional:evidence
npm run qa:functional:evidence:browser
npm run qa:functional:integration-mapping
npm run qa:functional:integration-mapping:browser
npm run qa:functional:load-plan:browser
npm run qa:functional:master-data
npm run qa:functional:master-data:browser
npm run qa:functional:rates
npm run qa:functional:rates:browser
npm run qa:functional:shell
npm run qa:functional:browser
npm run qa:functional:shell:browser
```

Planned module scripts:

```text
npm run qa:functional:catalog
npm run qa:functional:integration-mapping
npm run qa:visual
```

The repository should also expose backend-focused companions where useful:

```text
python -m pytest tests/test_gui_functional_contracts.py -q
python -m pytest tests/test_<module>_synthetic_e2e.py -q
```

Where the in-app Browser plugin is unavailable, the accepted fallback is a local
Playwright runner against local FastAPI + Vite. Evidence must record the failure
mode and fallback command when fallback is used.

## 8. Fixture And Data Rules

Functional GUI QA must use synthetic fixtures only.

```text
- No real client names.
- No CNPJ/CPF or production-like identifiers.
- No customer local paths.
- No real integration credentials.
- No screenshots that reveal customer data.
- Generated files must use synthetic payloads and client-safe filenames.
```

Synthetic seed data should be created through backend setup helpers or API
contracts, not by frontend-only mocks, for Layer 2 journeys.

## 9. Acceptance For A Module Journey

A module journey is ready when it records:

```text
- Linear issue id.
- Route and user role.
- Backend APIs used.
- Synthetic data setup.
- Primary action path.
- Expected backend state transition.
- Expected UI state transition.
- Navigate-away and return-state assertion.
- Error/blocked-state assertion.
- Console/runtime result.
- Evidence/artifact assertion, when applicable.
- Remaining risk or missing API.
```

## 10. Recommended Execution Order

```text
1. Shell foundation: DONE through OTM-99, OTM-101, OTM-103.
2. Rates create-validate-export journey: OTM-102.
3. Catalog lookup/validation journey: OTM-90.
4. Platform/Admin setup/jobs/audit journey: OTM-97.
5. Integration Mapping authoring journey: OTM-96.
6. Load Plan/Cutover/CSVUTIL journey: OTM-92.
7. Master Data, Assets, Evidence, and Order Release module journeys.
```
