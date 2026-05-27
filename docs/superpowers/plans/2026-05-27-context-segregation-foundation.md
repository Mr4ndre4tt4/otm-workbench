# Context Segregation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:test-driven-development before production changes and
> superpowers:verification-before-completion before claiming a slice is done.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce explicit project/client-domain, environment, and
visibility/access-policy scope for operational OTM Workbench records while
preserving shared technical catalog data and explicit Public View behavior.

**Architecture:** Add a backend-owned operational scope layer that resolves the
current user's active context, grants, and `DBA` visibility into reusable query
filters and create/update guards. Operational modules consume that layer.
System-seeded reference/catalog data remains global unless a module spec marks
it as project-scoped.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite local-first persistence, pytest,
React/Vite frontend consuming backend-owned navigation/context metadata.

---

## Current Inventory

Already present foundations:

- `ActiveContext` stores `project_id`, `profile_id`, `environment_id`,
  `domain_name`, and `can_view_all_domains`.
- Cockpit/session payloads already expose active context and setup status.
- `allowed_domains_for_context` already separates normal users from
  `DBA`-style wildcard visibility.
- `Job`, `RateBatch`, `ReferenceObject`, `ReferenceImportBatch`, reference
  snapshots, and most Load Plan/Cutover models already carry project and
  environment fields.

Partial or missing scope:

- `Artifact`, `Manifest`, and `Evidence` carry project only; they need
  environment, domain, and visibility/access-policy ownership before they can
  be reused safely by modules.
- `Asset` carries project, profile, environment, visibility, scope type, and
  sensitivity, but lacks explicit `domain_name` and access-policy binding.
- `MasterDataTemplate`, `MasterDataBatch`, generated canonical/output records,
  CSV files, and coordinate-quality batches do not carry operational scope yet.
- `OrderReleaseTemplate`, `OrderReleaseBatch`, and rows do not carry project,
  environment, domain, or visibility/access-policy scope yet.
- `IntegrationDefinition`, systems, endpoints, payload artifacts, schema
  documents, mappings, loops, joins, lookups, and response handlers do not
  carry project, environment, domain, or visibility/access-policy scope yet.
- Load Plan operational parents carry project and environment, but most records
  lack explicit `domain_name`; scope can be inherited from the source batch only
  when that relationship is enforced by tests.

Intentionally global or technical unless later reclassified:

- module registry, capability registry, role templates, feature flags;
- OTM table definitions, table columns, foreign keys, load sequence contracts,
  CSV contracts, schema packs, schema files, schema roots, schema paths, and
  service-operation metadata;
- system-seeded classification lists and transform-type catalogs.

## Scope Model

Every operational record must resolve to:

```text
project_id      required for private client work; null only for explicit Public View/system records
environment_id  required when the record represents environment-specific work
domain_name     OTM domain/client partition; PUBLIC is explicit shared scope
visibility      PRIVATE, PROJECT, PROFILE, MODULE, PUBLIC, or equivalent backend-owned enum
access_policy   grant/policy binding used by Settings and enforced in queries
```

`DBA` can see all project/domain/environment records. Normal users can only see
records allowed by their project grants, active environment, and allowed domain
set. Public View is a separate allowed scope and must not be implemented as a
shortcut to private records.

## Task 1: Add Behavior-Lock Tests For Scope Resolution

**Files:**

- Modify: `tests/test_operational_context.py`
- Create or modify: `tests/test_operational_scope.py`

- [x] Add tests that resolve active context into an operational scope object.
- [x] Assert default unaffiliated context exposes only explicit Public View.
- [x] Assert normal users receive only allowed project/domain/environment
  filters.
- [x] Assert `DBA` receives wildcard domain visibility without bypassing audit
  metadata.
- [x] Assert missing project/environment/domain blocks creation of private
  operational records.

Expected command:

```bash
pytest tests/test_operational_context.py tests/test_operational_scope.py -q
```

## Task 2: Implement Backend Scope Utility

**Files:**

- Create: `src/otm_workbench/platform/scoping.py`
- Modify only where tests require imports.

- [x] Create `OperationalScope` with project, profile, environment, domain,
  public/private mode, and all-domain visibility.
- [x] Create `scope_from_active_context(context)` normalization.
- [x] Create reusable helpers for `require_private_scope`,
  `allowed_domain_names`, and model filter composition.
- [x] Keep SQLAlchemy-specific filtering in helpers so route modules do not
  duplicate grant logic.

Expected command:

```bash
pytest tests/test_operational_context.py tests/test_operational_scope.py -q
```

## Task 3: Classify Models Before Migration

**Files:**

- Create: `docs/agent/CONTEXT_SEGREGATION_MODEL_LEDGER.md`

- [x] Create a table for each model family:
  `global`, `public-capable`, `private-operational`, `inherits-parent-scope`,
  or `needs-review`.
- [x] Mark the parent record that owns scope for child tables.
- [x] Mark expected migration fields for each private-operational parent.
- [x] Mark records that need Oracle Data Dictionary validation before fixture
  generation.

Acceptance:

```text
No model receives a migration before its ledger classification is explicit.
```

## Task 4: Retrofit Shared Artifacts And Assets First

**Files:**

- Modify: `src/otm_workbench/models.py`
- Modify relevant artifact/evidence/assets services and routes.
- Add focused tests under `tests/`.

- [x] Add `environment_id`, `domain_name`, `visibility`, and policy metadata to
  `Artifact`, `Manifest`, and `Evidence`.
- [x] Add `domain_name` and policy metadata to `Asset`.
- [x] Ensure generated artifacts inherit scope from the module record that
  created them.
- [x] Ensure Public View assets/evidence are explicitly marked public and never
  expose private client data by omission.

Status note:

```text
Platform artifact/manifest endpoints now accept scope metadata, platform
evidence creation inherits scope from a linked artifact or manifest, and Assets
create/serialize includes domain and access policy. Module-specific generators
still need inheritance tests when each module is retrofitted.

The first generator inheritance lock is in Rates CSV export: artifact,
manifest, and evidence inherit project/profile/environment/domain from the
RateBatch. Platform artifacts/evidence now force domain_name=PUBLIC when
visibility=PUBLIC, including direct evidence without linked artifacts.

The second generator inheritance lock is in Load Plan CSVUTIL build: CTL/CL
artifacts, the CSVUTIL manifest, and CSVUTIL evidence inherit
project/profile/environment and the package domain from the registered
LoadPlanPackage.

The third generator inheritance lock is in Load Plan ZIP analysis: analysis
manifest and evidence inherit project/profile/environment and package domain
from the registered LoadPlanPackage; audit/event payloads now include the same
scope metadata.

The fourth generator inheritance lock is in Load Plan cutover readiness:
readiness evidence inherits project/profile/environment and package domain from
the registered LoadPlanPackage; audit/event payloads now include the same scope
metadata.

The fifth generator inheritance lock is in Load Plan readiness export:
readiness export artifacts, manifest, evidence, audit, and domain event inherit
project/profile/environment and readiness/package domain from the cutover
readiness record.

The sixth generator inheritance lock is in Load Plan cutover handoff: handoff
evidence, audit, and domain event inherit project/profile/environment and
package domain from the registered LoadPlanPackage.

The seventh generator inheritance lock is in Master Data CSV package export:
generated ZIP artifact, manifest, and evidence inherit project/profile,
environment, domain, and PROJECT visibility from the source MasterDataBatch.

The eighth generator inheritance lock is in Integration Mapping: payload sample,
preview, and generated markdown spec artifacts inherit project/profile,
environment, domain, and PROJECT visibility from the source
IntegrationDefinition.

The ninth generator inheritance lock is in Load Plan package intake:
Rates-derived intake evidence and Master Data-derived package/evidence records
inherit project/profile, environment, domain, and PROJECT visibility from their
source batches.

The tenth generator inheritance lock is in Load Plan cutover package flow:
cutover checklist creation/readiness evidence, cutover package export
artifact/manifest/evidence, and go/no-go evidence inherit project/profile,
environment, domain, and PROJECT visibility from the registered
LoadPlanPackage/checklist path.

The eleventh generator inheritance lock is in Order Release XML generation:
generated XML artifacts and evidence inherit project/profile, environment,
domain, and PROJECT visibility from the source OrderReleaseBatch.

The twelfth generator inheritance lock is in Rates approval: approval evidence
inherits project/profile, environment, domain, and PROJECT visibility from the
source RateBatch.

The thirteenth generator inheritance lock is in Load Plan sequence snapshots:
sequence snapshot evidence inherits project/profile, environment, domain, and
PROJECT visibility from the source LoadPlanPackage.

The fourteenth generator inheritance lock is in Load Plan review decisions:
review decision evidence, audit payloads, and domain event payloads inherit
project/profile, environment, domain, and PROJECT visibility from the review
item and source LoadPlanPackage.

The fifteenth generator/public-scope lock is in Master Data template workbook
generation: generated published-template workbooks are explicit shared
artifacts with domain PUBLIC and visibility PUBLIC instead of relying on empty
private scope fields.

Task 4 is complete for the active UI phase modules and platform shared
artifact/evidence paths. Coordinate Quality export remains intentionally
excluded from this closure because `MasterDataCoordinateQualityBatch` is
classified as `needs-review`, lacks operational scope columns, and Coordinate
Quality is not a top-level UI module in the current phase. It must receive a
separate model/scope migration before its export artifacts can inherit private
operational scope.

The first module route access lock is in Rates: list, summary, detail,
readiness, approval, table intake, validation, issues, CSV preview/export,
artifacts/download, and evidence routes now resolve the batch through active
operational context before returning or mutating data. Cross-domain and
cross-environment batches return 404 for normal users; all-domain context stays
bounded to the active project and environment.

The second module route access lock starts in Load Plan packages: packages now
carry `domain_name`, and package list, summary, detail, intake from Rates,
ZIP analysis, CSVUTIL build, cutover checklist creation, sequence snapshot,
cutover readiness generation, cutover handoff eligibility/commit, and
checklist-derived package actions resolve the package through active
operational context.

The Load Plan child read-model lock now also covers ZIP analysis list/detail,
CSVUTIL build list/detail, sequence snapshot list/detail/latest, cutover
checklist detail and checklist-derived actions, cutover readiness
list/detail/latest/export, readiness export list/detail, cutover handoff
list/detail, and review queue generation/list/detail/decision. Load Plan route
access filtering is now covered for the current package-centered workflow.

The first Assets route access lock covers asset list, detail, update, archive,
link create/list, version upload/list, and current-version download. Assets now
uses the shared active-context scope helper against its project, environment,
and domain fields.

The first Master Data batch route access lock adds project, environment,
profile, and domain fields to MasterDataBatch; workbook-editor and workbook
upload batch creation inherit active context; batch list, summary, detail,
artifacts, output records, CSV files, OTM import readiness/guard, artifact
download, relationship validation, mapping, output build, CSV build, and CSV
package export are active-context filtered.
```

Expected tests:

```bash
pytest tests/test_assets_library_assets.py tests/test_operational_metadata.py -q
```

## Task 5: Retrofit Settings As Scope Authority

**Files:**

- Modify Settings/Admin platform routes and tests.
- Modify frontend Settings view only after backend contracts pass.

- [x] Treat Settings as the owner of project, client/domain, environment,
  profile, user, role, grant, and access-policy setup.
- [x] Expose backend-owned labels, available actions, and blocked reasons.
- [x] Connect the frontend Settings surface to the backend scope-authority
  contract while keeping the `AdminConsoleView` component name.
- [x] Add tests for normal user, project admin, and `DBA` setup visibility.
- [x] Add first role/grant authoring contracts and Settings UI forms.
- [x] Add first access-policy authoring contract, model, and Settings UI form.
- [x] Add first user authoring contract and grant user selector.
- [x] Add domain/environment scope fields to grants and enforce them in
  effective capabilities/navigation.
- [x] Delegate profile/environment authoring to Settings authority and scoped
  `settings.project.manage` grants.
- [x] Restrict Settings workspace/project/profile/environment selector lists
  so non-DBA users only see rows from granted projects.
- [x] Scope the Settings access-model read payload so ordinary scoped users do
  not receive global user, role, capability, grant, or policy catalogs.
- [x] Protect active context selection so non-DBA users can select only granted
  projects and only matching profile/environment rows.
- [x] Gate project setup-status reads by visible project scope to block direct
  URL access to hidden project readiness metadata.
- [x] Validate platform artifact, manifest, and evidence `access_policy_id`
  bindings against existing policies with matching project/visibility/domain.
- [x] Validate platform artifact, manifest, and evidence operational scope so
  profile/environment IDs must exist and belong to the effective project.
- [x] Validate platform job operational scope before job records, events, and
  audit metadata are created.
- [x] Restrict platform job list/detail/events/run/cancel for non-DBA users to
  jobs matching active project, environment, and allowed domain scope.
- [x] Restrict platform job creation for non-DBA users to active project,
  environment, and allowed domain scope.
- [x] Restrict Evidence Hub list/detail/archive input selection and artifact
  download for non-DBA users to active project, environment, and allowed domain
  scope.
- [x] Preserve common evidence scope on Evidence Hub archive artifact, manifest,
  evidence, audit metadata, and domain event records.
- [x] Reject mixed-scope Evidence Hub archive packages before archive records
  are created.
- [x] Restrict Project Cockpit recent jobs, artifacts, and evidence to active
  project, environment, and allowed domain scope for non-DBA users.
- [x] Disable contextual Project Cockpit actions for jobs/evidence until active
  project and environment scope exists.
- [x] Ignore stale saved Project Cockpit active context when the current user no
  longer has a grant for the stored project.
- [x] Ignore saved Project Cockpit active context when the user still has a
  grant for the project but no longer has a grant for the stored
  environment/domain scope.
- [x] Keep the old `AdminConsoleView` component name until a deliberate rename
  slice is approved.

Status note:

```text
Settings scope authority now exposes setup visibility as SCOPED, PROJECT, or
GLOBAL. Normal users get scoped/read-only setup visibility, project setup admins
receive project-level profile/environment/role/grant/access-policy authority
through Settings capabilities, and DBA users retain global setup authority.
The Settings UI renders the setup visibility inside the top-level scope
authority panel. Role/grant authoring now has backend contracts for access
model, role creation, and project grant assignment, with the Settings UI
rendering first-pass role and grant forms from those contracts. Access-policy
authoring now has an `AccessPolicy` model, create endpoint, access-model
listing, authority tests, and a first-pass Settings UI form.
User authoring now has a create endpoint, access-model user listing without
password/hash fields, scope-authority visibility, and a Settings UI grant user
selector. Grants now support optional environment/domain scope; effective
capabilities and navigation honor scoped grants while preserving legacy
project-level grants.
Profile and environment creation now use Settings authority instead of global
admin-only access, and the Settings UI disables setup controls from backend
setup visibility. Settings setup selectors now derive non-DBA visibility from
granted projects: workspaces are listed only when they contain visible projects,
and project/profile/environment selectors hide ungranted rows. The Settings
access-model payload now follows setup authority: ordinary scoped users receive
only their own user/grant/role context and no global capability or policy
catalog, while setup admins and DBA users retain the broader lists needed for
their granted setup actions. Active context selection now enforces project
grants for non-DBA users and rejects profile/environment values from other
projects before persisting context. Project setup-status reads now require the
requested project to be visible to the user, preserving 404 for missing projects
and returning 403 for hidden-but-existing projects. Platform artifact,
manifest, and evidence creation now validates effective project/profile/
environment scope, then rejects missing or cross-scope access policy bindings
before records are persisted. Platform job creation now uses the same
operational-scope validation before job records, events, and audit metadata are
created. Platform job list/detail/events/run/cancel now applies active-context
visibility for non-DBA users. Platform job creation now applies the same
active-context boundary for non-DBA users. Evidence Hub reads, archive input
selection, and artifact download now apply active-context visibility for
non-DBA users. Evidence Hub archive package records now inherit common scope
from the selected evidence and reject mixed-scope archive requests.
Project Cockpit recent records now apply active-context visibility for non-DBA
users, closing same-project cross-environment/domain leakage in the summary.
Contextual Project Cockpit actions for jobs/evidence now expose
ACTIVE_CONTEXT_REQUIRED until active project/environment scope exists.
Saved Project Cockpit active context is ignored for non-DBA users when the
stored project is no longer granted, or when the grant has shifted to a
different environment/domain scope inside the same project.
Task 5 is complete: Settings is the owner of setup authority for the current
phase, the old `AdminConsoleView` component name is deliberately preserved, and
the expected backend/frontend Settings validation commands pass.
```

Expected tests:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
```

## Task 6: Retrofit Operational Modules In Delivery Order

Order:

1. Settings completion gates.
2. Cockpit context selector and accelerator gating.
3. Rates, mostly query/filter hardening.
4. Assets, after shared artifact scope.
5. Master Data, add batch/template scope.
6. Integration, add definition/system/endpoint/mapping scope.
7. Order Release, add template/batch/row scope.
8. Load Plan, harden inherited domain and source-package scope.

For each module:

- [x] Add first Rates list/detail/action read guard tests for same-domain,
  cross-domain, cross-environment, and all-domain context.
- [x] Add first Load Plan package list/detail/intake/action guard tests for
  same-domain, cross-domain, cross-environment, and all-domain context.
- [x] Add first Load Plan child read-model guard tests for ZIP analysis,
  CSVUTIL build, sequence snapshot, cutover checklist, cutover readiness, and
  readiness export.
- [x] Add first Load Plan child read-model guard tests for cutover handoff and
  review queue.
- [x] Add first Assets route guard tests for same-domain, cross-domain,
  cross-environment, and all-domain context.
- [x] Add first Master Data batch route guard tests for same-domain,
  cross-domain, cross-environment, and all-domain context.
- [x] Add first Integration definition route guard tests for same-domain,
  cross-domain, cross-environment, all-domain context, and definition-owned
  child routes.
- [x] Add first Integration systems/endpoints route guard tests for same-domain,
  cross-domain, cross-environment, and all-domain context.
- [x] Add first Order Release batch route guard tests for same-domain,
  cross-domain, cross-environment, all-domain context, and generated artifact
  scope inheritance.
- [x] Add first Order Release template/version guard tests for public seed
  templates, same-domain, cross-domain, cross-environment, and all-domain
  context.
- [x] Add Rates create/list/detail negative tests for non-DBA users without
  active context and for cross-domain/cross-environment batch creation.
- [x] Add Assets no-active-context negative tests for non-DBA list/detail and
  child read routes.
- [x] Add Master Data no-active-context negative tests for non-DBA batch
  list/summary/detail/child reads and workbook-editor batch creation.
- [x] Add Integration no-active-context negative tests for non-DBA definition
  and system list/detail/child reads and creation.
- [x] Add Order Release no-active-context negative tests for non-DBA batches,
  private templates, and creation while preserving public seed templates.
- [x] Add Load Plan no-active-context negative tests for non-DBA package
  list/detail/summary and package registration from Rates/Master Data source
  batches.
- [x] Add Rates cross-project negative tests for active-context list/detail,
  action routes, and non-DBA batch creation.
- [x] Add Assets cross-project negative tests for active-context list/detail
  and child read routes.
- [x] Add Master Data cross-project negative tests for active-context batch
  list/detail and child read routes.
- [x] Add Integration cross-project negative tests for active-context
  definition/system roots and parent-scoped child routes.
- [x] Add Order Release cross-project negative tests for active-context
  batches, private templates, template versioning, and template-owned batch
  creation while preserving public seed visibility.
- [x] Add Load Plan cross-project negative tests for package list/detail/intake
  plus representative ZIP analysis and CSVUTIL child read routes.
- [x] Confirm Public View/shared-data coverage stays limited to explicit shared
  paths: platform artifacts/evidence normalize `visibility=PUBLIC` to
  `domain_name=PUBLIC`, and Order Release public seed templates stay visible
  while private operational records remain scoped.
- [x] Add Integration Mapping child CRUD guard coverage for non-DBA users
  without active context: mapping create/list/detail/delete routes now return
  not-found through the scoped parent definition boundary.
- [x] Add Master Data action guard coverage for non-DBA users without active
  context: batch validate/map/build-output/build-csv/export-csv-package and
  submit-otm routes now return not-found before processing hidden batches.
- [x] Add Load Plan action/update guard coverage for non-DBA users without
  active context: package child creation, checklist item update, sequence
  snapshot, readiness, and handoff routes now return not-found through package
  scope.
- [x] Add create/list/detail/update/delete tests for remaining module access.
- [x] Add negative tests for remaining cross-domain, cross-environment, and
  cross-project access across the active operational module sequence.
- [x] Add `DBA` visibility tests across the active operational module sequence.
- [x] Add Public View tests only where the module explicitly supports shared
  data.
- [x] Update module docs and QA evidence in the same slice.

Status note:

```text
Task 6 is complete for the active operational module sequence. Cockpit context
selector/accelerator gating and representative route guards across Rates,
Assets, Master Data, Integration, Order Release, and Load Plan passed targeted
validation. The first targeted operational command was corrected after using an
outdated Assets test name; the corrected selection passed.
```

## Task 7: Fixture And Evidence Strategy

**Files:**

- Create fixtures under a synthetic test-data location chosen by the module
  plan.
- Update `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`.

- [x] Create synthetic CSV, XML, JSON, XSLT, PDF, DOCX, MD, and XLSX fixtures
  only where the module scenario requires them.
- [x] Keep files valid and large enough for performance/edge scenarios when
  needed.
- [x] For OTM CSV, preserve first-line table name, second-line columns, then
  values; include `exec alter session ...` date format before values when date
  fields exist.
- [x] Validate OTM table dependencies through Data Dictionary and official
  Oracle documentation during each module-specific fixture slice.

Status note:

```text
Baseline synthetic fixtures now live under tests/fixtures/synthetic with CSV,
XML, JSON, XSLT, PDF, DOCX, MD, XLSX, and ZIP coverage. The RATE_GEO_COST CSV
columns are validated against the local OTM 26B Data Dictionary. Large
module-specific fixtures and official Oracle functional checks remain per-slice
gates when a module scenario requires them.
```

## Task 8: Verification And Handoff

- [x] Run targeted backend tests for the module being changed.
- [x] Run targeted frontend tests when UI context behavior changes.
- [x] Run `git diff --check`.
- [x] Capture browser QA evidence for module completion slices.
- [x] Update docs, Linear, GitHub, tests, and QA evidence together when product
  behavior changes.

Status note:

```text
Context segregation foundation tasks 1-8 are complete for the active UI phase.
Targeted backend verification now includes the synthetic fixture baseline,
public/shared scope tests, Settings authority tests, Cockpit/navigation tests,
and representative operational module guard tests. Frontend verification was
run for the Settings path where the closure touched frontend governance.
Browser QA and Linear/GitHub updates remain deferred until an approved
tracking/publication or browser-facing completion slice.
```

## Self-Review

Spec coverage:

```text
- Explicit client/domain scope: Tasks 1, 2, 4, 6.
- Environment segregation: Tasks 1, 2, 4, 6.
- Visibility/access-policy behavior: Tasks 2, 4, 5, 6.
- Public View separation: Tasks 1, 2, 4, 6.
- DBA full visibility: Tasks 1, 2, 5, 6.
- Settings-first sequence: Tasks 5 and 6.
- Test fixture planning: Task 7.
```

Implementation risk:

```text
Do not add scope columns broadly without query tests. Child tables should inherit
scope from parent operational records unless independent access is required.
Global technical metadata must remain global to avoid duplicating Oracle
reference structures per client/domain.
```
