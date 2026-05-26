# GUI Module API Contract Matrix

**Status:** delivered  
**Linear:** `OTM-88`, completed under `OTM-86`
**Scope:** backend API contracts consumed by GUI module journeys and readiness gaps.

## Purpose

This matrix keeps backend-owned contracts visible while GUI modules evolve. It
maps each implemented route family to the frontend hooks/views that consume it,
the current QA coverage, and the remaining explicit scope.

It is not an OpenAPI replacement. It is the product-facing readiness map used to
decide whether a GUI module is functionally connected to the backend story it
claims to support.

## Contract States

```text
READY        Backend contract is implemented, consumed by GUI, and covered by functional QA.
BACKEND      Backend contract exists, but GUI does not yet expose it in the accepted journey.
FUTURE       Purpose is known, but work should wait for explicit new scope or governance.
```

## Platform And Shell

| Area | Backend contract families | Frontend consumers | QA baseline | State | Notes |
|---|---|---|---|---|---|
| Auth/session | `POST /api/v1/platform/session/login`, `GET /session/me` | `useAuth`, shell route gate | `AppFunctionalShell.test.tsx`, `test_gui_shell_backend_contracts.py`, shell browser QA | READY | GUI does not own auth decisions. |
| Navigation/icons | `GET /api/v1/platform/navigation`, `GET /modules` | `useNavigation`, `WorkbenchShell`, `SidebarNav` | shell tests, navigation backend tests | READY | Labels and icon keys are backend-owned; sidebar no longer renders raw lifecycle chips. |
| Context/preferences | `GET/POST /active-context`, `GET/PUT /user-preferences`, `GET /active-context/capabilities` | `ContextSummary`, `ContextSwitcher`, `PreferenceControls`, `WorkbenchShell` | shell tests, operational context tests | READY | Theme/density/sidebar persistence is backend-owned. |
| Cockpit/admin platform | `/project-cockpit/summary`, `/workspaces`, `/projects`, `/profiles`, `/environments`, `/feature-flags`, `/jobs`, `/audit-logs` | Project Cockpit and Admin Console | admin/shell browser QA, operational metadata tests | READY | Advanced edit/delete/pagination remains explicit future scope. |

## Module Matrix

| Module | Backend contract families | Frontend consumers | Functional QA | State | Remaining explicit scope |
|---|---|---|---|---|---|
| Rates Studio | `/api/v1/modules/rates/summary`, templates, batches with optional official schema-root companions, readiness, approval, table rows, validation with schema-root summary, issues, CSV preview/export, artifacts/download, evidence, dictionary/reference helpers | `frontend/src/platform/hooks/rates.ts`, `RatesStudioView` | Rates React + browser QA, rates backend tests | READY | Current MVP0 functional journey complete. Data Dictionary remains source of truth for CSV/table semantics; schema roots are companion guidance only. |
| Catalog Core | `/api/v1/catalog/tables`, columns, reference options, macro objects, macro tables, macro load plan, validate table/column/reference | `catalog.ts`, `CatalogCoreView` | Catalog React + browser QA, `test_catalog_core.py` | READY | Reference option browser can be added only as explicit enhancement. |
| Master Data / Data Factory | templates with available_actions and optional official schema-root guidance, drafts, versions, publish, validate definition with schema-root summary, workbook build, workbook editor contract/validate/batch creation, batches with available_actions, filter-only batch summary, relationship validation, map, output, CSV build/preview/export, artifacts/download, scenario packs, guarded direct OTM import readiness/submit refusal | `masterData.ts`, `MasterDataView` | Master Data React + browser QA, master data/direct-import-guard/load-plan intake tests | READY | OTM-115 completion acceptance met for MVP0. Real governed direct OTM submission, richer audited spreadsheet editing, fuller schema-path UI hints, and deeper history analytics are future scope. |
| Coordinate Quality | `/api/v1/modules/master-data/coordinate-quality/validate`, batches, results, export | `coordinateQuality.ts`, embedded Quality stage | Coordinate Quality React + browser QA, coordinate backend tests | READY | External provider setup and map diagnostics are future scope. |
| Load Plan / Cutover | packages from Rates/Master Data, package list/detail/summary, checklist templates/detail/item patch/readiness/export, CSVUTIL builds, ZIP analysis, review queue, sequence snapshots, readiness exports, Go/No-Go, handoff eligibility/commit | `loadPlan.ts`, `LoadPlanView` | Load Plan React + browser QA, load plan/cutover/CSVUTIL tests | READY | Treat additional work as hardening or explicit new scope. |
| Assets Library | classifications, assets list/detail/create/update/archive, versions, links, download, Catalog/Data Dictionary/Evidence Hub target validation | `assets.ts`, `AssetsLibraryView` | Assets React + browser QA, assets backend tests | READY | Target pagination/virtualization only if filtered target volume requires it. |
| Evidence Hub | evidence list/detail/filter, artifact download, archive package creation, archive history via evidence records | `evidence.ts`, `EvidenceHubView` | Evidence React + browser QA, evidence backend tests | READY | Archive detail/audit drill-down only if archives become first-class investigation objects. |
| Order Release Generator | templates with optional official `Transmission`/`Release` schema-root references, batches, preview XML with schema-root envelope validation summary, generate XML artifact, artifacts/download, guarded OTM submit | `orderReleaseGenerator.ts`, `OrderReleaseGeneratorView` | OR React + browser QA, OR backend tests | READY | Richer row/template authoring, deeper XSD validation, and governed direct OTM submit remain future scope. |
| Integration Mapping Studio | systems/endpoints, definitions with optional source/target official `SchemaRoot` references, payload artifacts, schema parse/docs/nodes, Catalog Core official source root/path browsing with required/repeatable/documentation metadata, mappings with backend-owned transform_config, loops, joins, join bindings, lookups, validate with spec/preview readiness and stale schema-root blockers, direct scalar/single-loop/lookup executable preview with provenance, mixed scalar mapping+lookup preview, scalar and loop-scoped join guard provenance, explicit multi-hop join-binding provenance, scalar and loop-scoped alias mappings from join bindings, loop-scoped MOCK lookup execution, CONSTANT/DATE_FORMAT/CONCAT transform execution, FILTER_BY_QUALIFIER refnum extraction, COUNT_DISTINCT filtered aggregation, metadata-only preview fallback, spec, artifacts/download | `integrationMapping.ts`, `catalog.ts`, `IntegrationMappingView` | Integration Mapping React + browser QA, integration backend tests | BACKEND | OTM-130 added persisted transform config; OTM-131/132/136/137/138/139/140 added executable preview slices; OTM-133/134/135 execute CONSTANT, OTM_GLOGDATE -> ISO8601 DATE_FORMAT, and controlled CONCAT. OTM-145 delivered qualifier-based extraction and count-distinct aggregation. OTM-147 added backend join-binding CRUD plus scalar preview provenance; OTM-148 exposes join-binding authoring and grouped review in the staged Rules UI; OTM-149 adds scalar alias mappings; OTM-150 adds loop-scoped alias mappings for `$.deliveries[]` style target rows; OTM-151 adds validation blockers for missing/out-of-scope aliases and a UI alias source selector for mapping authoring. Schema Pack first-consumer backend contract added official root references on definitions; first Rules-stage official source path picker now consumes Catalog Core paths and displays Catalog-owned path metadata. Remaining hardening is fuller scenario QA, target path picker, and richer required-field semantics. |

## Cross-Module Contracts

| Contract | Backend owner | GUI consumers | State | Rule |
|---|---|---|---|---|
| Artifact download | Module routes plus Evidence Hub guarded artifact endpoints | Rates, Master Data, Load Plan, Assets, Evidence, OR, Integration Mapping | READY | GUI must not expose local filesystem paths. |
| Evidence records | Platform evidence writer plus Evidence Hub reader/archive | Rates, Master Data, Load Plan, Assets, Evidence | READY | Client-safe metadata only; no real client data in fixtures or QA. |
| Load sequencing | Catalog Core load plan, Rates dictionary sequence, Load Plan package sequence | Catalog, Rates, Master Data, Load Plan | READY | OTM table order remains backend/data-dictionary driven. |
| Cutover handoff | Load Plan checklist/readiness/export/archive/handoff | Master Data handoff registration, Load Plan | READY | Handoff commit is disabled unless backend eligibility is true. |
| User preferences | Platform preferences | Shell, sidebar, topbar controls | READY | No durable preference may live only in frontend state. |

## Readiness Decisions

```text
- The route journey matrix is the QA source of truth.
- A module marked READY here still needs explicit new scope before expanding
  beyond its accepted journey.
- If a frontend view calls a backend endpoint, it must be covered by either
  React functional tests, browser functional QA, backend tests, or a documented
  reason why the endpoint is out of the accepted journey.
- If a backend endpoint exists but is not in a GUI journey, do not add UI for it
  opportunistically; create or update a Linear issue first.
```

## Current Open Follow-Ups

```text
OTM-92 closed after Load Plan READY validation.
OTM-98 implemented artifact trust-boundary hardening for platform helpers and Evidence Hub downloads.
OTM-86 closed after all module route families reached accepted READY journeys or explicit future scope.
```
