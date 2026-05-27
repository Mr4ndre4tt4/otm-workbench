# Decision Log

**Status:** active
**Date:** 2026-05-27

## 2026-05-27: Require Chat Continuity Intake And Handoff Capsules

Status:
accepted governance guardrail

Change type:

```text
validation strategy change
delivery pipeline change
documentation change
```

Problem:
When work continues in a new chat, inherited conversational memory can be
missing, compressed, stale, or disconnected from the actual worktree. A new
agent can then continue from partial context, miss a correction, trust stale
evidence, overwrite user-owned changes, or skip validation.

Decision:
Add a mandatory chat-continuity workflow. Previous chats that change behavior,
docs, tests, QA evidence, Linear, GitHub, or design artifacts must leave a
handoff capsule in `docs/agent/HANDOFF.md`. New chats must rebuild context from
durable sources before implementation or acceptance claims.

New-chat source order:

```text
user's latest instruction
-> repository code and tests
-> active docs under docs/agent/
-> external boards/tools only after verification
-> inherited chat memory
```

Required new-chat intake:

- read `AGENTS.md`;
- read `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`;
- read latest `HANDOFF.md` and `VALIDATION_REPORT.md`;
- inspect `DECISION_LOG.md`, `RISK_REGISTER.md`, `CURRENT_SCOPE.md`, and
  `DELIVERY_PIPELINE.md`;
- run `git status --short`;
- inspect relevant diffs before editing;
- apply the runtime freshness gate before browser screenshots;
- state the recovered current state before proceeding.

Impacted docs:

- `AGENTS.md`
- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/CHANGE_CONTROL.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/DOCUMENT_INVENTORY.md`

Status:
Active immediately for future sessions.

## 2026-05-27: Require Runtime Freshness Before Browser Evidence

Status:
accepted validation guardrail

Change type:

```text
validation strategy change
delivery pipeline change
documentation change
```

Incident:
A browser screenshot for the Assets slice showed excluded top-level modules
(`Evidence Hub`, `OTM Catalog Core`, `Admin Console`, and `Developer Tools`) in
the sidebar. Source navigation rules already filtered those modules, but the
browser was connected to an older local backend process that had been started
before the current navigation whitelist.

Decision:
Browser QA evidence is valid only after a runtime freshness check proves the
live backend/frontend pair matches current scope. Agents must query the live
`/api/v1/platform/navigation` endpoint used by browser QA, compare returned
module IDs with the current UI phase and role permissions, and restart the
backend/dev server or move to a fresh port before screenshots when there is any
mismatch.

Correct current UI phase:

```text
Cockpit
Master Data / Data Factory
Rates Studio
Load Plan / Cutover
Integration Mapping Studio
Order Release Generator
Assets Library
Settings
```

Out of top-level UI for this phase:

```text
Catalog Core
Evidence Hub
separate Admin Console / Jobs
Developer Tools
Coordinate Quality as a top-level module
generic dashboards
```

Validation:

```powershell
pytest tests/test_modules_navigation.py -q
npm test -- src/app/AppFunctionalAssets.test.tsx
```

Runtime verification after backend restart:

```text
live navigation ids for the demo context:
master_data, home, rates, load_plan, assets, order_release_generator,
integration_mapping
```

Notes:
`Settings` can be absent for a given runtime user when that user lacks the
needed setup capability; the freshness gate compares the current scope against
the selected role's permissions, not just a global list.

Impacted docs:

- `AGENTS.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/DOCUMENT_INVENTORY.md`

Follow-up:
Future browser QA records should include backend URL, frontend URL, user
context, and navigation freshness result before screenshots are treated as
acceptance evidence.

## 2026-05-27: Start Assets Hub And Library Route Split

Status:
accepted local implementation slice

Area:
assets module completion

Decision:
`/assets` now behaves as the Assets Library hub, while `/assets/library`
preserves the existing backend-backed workflow as a temporary library route.

Rationale:
The consolidated Assets spec says the hub should orient users and should not
host the full asset lifecycle. Moving the whole lifecycle at once would create
too much blast radius, so this first slice creates the route boundary while
keeping existing create/version/link/download/archive behavior available.

Validation:

```text
npm test -- src/app/AppFunctionalAssets.test.tsx -t "renders an Assets hub"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
npm run qa:functional:assets:browser
```

Tracking:

- Linear OTM-167 comment `762eda83-cab1-4532-b1ed-e4801392105f`

Files:

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/TASK_CONTRACT_ASSETS_HUB_LIBRARY.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/DECISION_LOG.md`
- `var/qa/assets-hub-library-route.png`

Follow-up:
Extract asset detail, create/edit, versions, links, classifications, and
archive into route-level screens.

## 2026-05-27: Cover Load Plan Cross-Project Package Guards

Change type:

```text
load plan module hardening
cross-project regression-test addition
```

Decision:

Load Plan now has explicit cross-project regression coverage for package
list/detail/intake and representative child read models, including ZIP analysis
and CSVUTIL builds.

Reason:

Load Plan package scope is the parent boundary for sequence, cutover,
readiness, handoff, review queue, ZIP analysis, and CSVUTIL flows.
Cross-project coverage proves those workflows cannot be reached through a
package outside the active project.

Validation:

```bash
pytest tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail_follow_active_context_scope -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_load_plan_package_intake.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Cover Order Release Cross-Project Scope Guards

Change type:

```text
order release module hardening
cross-project regression-test addition
```

Decision:

Order Release now has explicit cross-project regression coverage for operational
batches, private templates, template versioning, and batch creation from a
private template. Public seed templates remain visible while private templates
outside the active project stay hidden.

Reason:

Order Release has both shared seed templates and scoped operational authoring
records. Cross-project coverage ensures the public/private split remains
intentional and does not leak private templates or generated batch workflows.

Validation:

```bash
pytest tests/test_order_release_generator_batches.py::test_order_release_batches_follow_active_context_scope -q
pytest tests/test_order_release_generator_foundation.py::test_order_release_templates_follow_active_context_scope -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_order_release_generator_batches.py`
- `tests/test_order_release_generator_foundation.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Cover Integration Cross-Project Scope Guards

Change type:

```text
integration module hardening
cross-project regression-test addition
```

Decision:

Integration Mapping now has explicit cross-project regression coverage for
definition and system roots plus their parent-scoped child routes. Definitions
and systems outside the active project remain hidden even with matching domain
and environment type.

Reason:

Integration roots own mappings, endpoints, payload artifacts, schema documents,
loops, joins, lookups, response handlers, previews, and generated specs.
Cross-project coverage proves those child surfaces inherit the project boundary.

Validation:

```bash
pytest tests/test_integration_mapping_definitions.py::test_integration_definitions_follow_active_context_scope -q
pytest tests/test_integration_mapping_systems.py::test_integration_systems_and_endpoints_follow_active_context_scope -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_integration_mapping_definitions.py`
- `tests/test_integration_mapping_systems.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Cover Master Data Cross-Project Batch Guards

Change type:

```text
master data module hardening
cross-project regression-test addition
```

Decision:

Master Data now has explicit cross-project regression coverage for active-context
batch list/detail and child read routes. Batches from another project remain
hidden even when they share the same domain and environment type.

Reason:

Master Data batch children include output records, CSV files, validation,
mapping, export, and import-readiness flows. Cross-project coverage proves those
flows continue to inherit the project boundary from the batch.

Validation:

```bash
pytest tests/test_master_data_templates.py::test_master_data_batches_follow_active_context_scope -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_master_data_templates.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Cover Assets Cross-Project Scope Guards

Change type:

```text
assets module hardening
cross-project regression-test addition
```

Decision:

Assets now has explicit cross-project regression coverage for active-context
list/detail and child read routes. Assets outside the active project remain
hidden even when they share the same environment name and domain.

Reason:

Assets can link supporting files, OTM references, artifacts, evidence, versions,
and downloads. Cross-project coverage makes sure those child surfaces continue
to inherit the project boundary from the asset record.

Validation:

```bash
pytest tests/test_assets_library_assets.py -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_assets_library_assets.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Cover Rates Cross-Project Scope Guards

Change type:

```text
rates module hardening
cross-project regression-test addition
```

Decision:

Rates now has explicit cross-project regression coverage for list/detail/action
reads and non-DBA batch creation. Active-context scoped users can see and
create only inside the active project, environment, profile, and domain
boundary.

Reason:

Cross-domain and cross-environment tests were already present, but cross-project
coverage makes the client/domain isolation guarantee explicit for the first
operational module in the delivery order.

Validation:

```bash
pytest tests/test_rates_batches.py -q
```

Impacted docs and tests:

- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_rates_batches.py`

Status:

Implemented as regression coverage; no backend behavior change was required.

## 2026-05-27: Require Active Context For Non-DBA Load Plan Packages

Change type:

```text
access-control behavior change
load plan module hardening
regression-test addition
```

Decision:

Load Plan package list/detail/summary and package registration now hide
operational records from non-DBA users without active context. Package intake
from Rates and Master Data now resolves the source batch through scoped queries
before creating a Load Plan package.

Reason:

Load Plan packages are the root scope for sequence, ZIP analysis, CSVUTIL,
cutover checklist, readiness, handoff, and review queue records. If package
visibility falls through without active context, every child workflow can be
reached through an unscoped root.

Validation:

```bash
pytest tests/test_load_plan_package_intake.py::test_load_plan_packages_require_active_context_for_non_admin_access_and_register -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_load_plan_package_intake.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Require Active Context For Non-DBA Order Release Records

Change type:

```text
access-control behavior change
order release module hardening
regression-test addition
```

Decision:

Order Release batches now hide operational records from non-DBA users without
active context, and batch/template creation requires active project/environment
context for non-DBA users. Public seed templates remain visible without active
context, while private templates are hidden and cannot be versioned through a
stale/no-context route.

Reason:

Order Release batches and private templates are operational authoring records
that must carry explicit client/domain and environment scope. Public seed
templates are shared metadata and remain available as the module entry point.

Validation:

```bash
pytest tests/test_order_release_generator_batches.py::test_order_release_batches_require_active_context_for_non_admin_access_and_create -q
pytest tests/test_order_release_generator_foundation.py::test_order_release_templates_keep_public_seed_but_hide_private_without_active_context_for_non_admin -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_order_release_generator_batches.py`
- `tests/test_order_release_generator_foundation.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Require Active Context For Non-DBA Integration Records

Change type:

```text
access-control behavior change
integration module hardening
regression-test addition
```

Decision:

Integration Mapping definition and system list/detail routes now hide
operational records from non-DBA users without active context. Definition and
system creation now requires an active project/environment context for non-DBA
users, and child routes continue to be guarded through the scoped parent.

Reason:

Integration definitions and systems describe implementation-specific payloads,
systems, endpoints, mappings, and generated artifacts. They must not be listed,
opened, or created outside an explicit client/domain and environment scope.

Validation:

```bash
pytest tests/test_integration_mapping_definitions.py::test_integration_definitions_require_active_context_for_non_admin_access_and_create -q
pytest tests/test_integration_mapping_systems.py::test_integration_systems_require_active_context_for_non_admin_access_and_create -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_integration_mapping_definitions.py`
- `tests/test_integration_mapping_systems.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Require Active Context For Non-DBA Master Data Batches

Change type:

```text
access-control behavior change
master data module hardening
regression-test addition
```

Decision:

Master Data batch list/detail and child read routes now hide operational
batches from non-DBA users without active context. Workbook-editor and workbook
upload batch creation now require active project/environment context for
non-DBA users.

Reason:

Master Data batches are operational records and must not be visible or created
without explicit client/domain and environment scope. Seeded templates remain
readable as shared module metadata, but batch records require active context.

Validation:

```bash
pytest tests/test_master_data_templates.py::test_master_data_batches_require_active_context_for_non_admin_access_and_create -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_master_data_templates.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Hide Assets Without Active Context For Non-DBA Users

Change type:

```text
access-control behavior change
assets module hardening
regression-test addition
```

Decision:

Assets list/detail and child read routes now hide operational assets from
non-DBA users when no active context exists. The list returns empty and detail,
links, versions, and download routes return the existing not-found contract.

Reason:

Assets are operational records carrying project, environment, domain, and
visibility scope. A scoped user without active context must not fall through to
an unfiltered asset query.

Validation:

```bash
pytest tests/test_assets_library_assets.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_assets_library_assets.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Require Active Context For Non-DBA Rates Batch Access

Change type:

```text
access-control behavior change
rates module hardening
regression-test addition
```

Decision:

Rates batch list/detail access now returns no operational batches to non-DBA
users without an active context. Rates batch creation for non-DBA users now
requires an active project/environment context and rejects creation outside the
active project, environment, profile, or allowed domain scope.

Reason:

Rates is an operational module. Without an active context, a scoped user should
not inherit a broad query or create batches in arbitrary client/domain and
environment scopes.

Validation:

```bash
pytest tests/test_rates_batches.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_rates_batches.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Validate Cockpit Active Context Against Current Scope Grant

Change type:

```text
access-control behavior change
project cockpit hardening
regression-test addition
```

Decision:

Project Cockpit now treats a saved active context as absent when the current
non-DBA user's grants no longer cover the stored environment and domain, even
if the user still has a different grant for the same project.

Reason:

Project-level grant checks are not enough once grants can be scoped by
environment and domain. A context saved under `DEV/OTM1` must not continue to
expose setup status, recent jobs, artifacts, or evidence after the user's grant
is shifted to `UAT/OTM2`.

Validation:

```bash
pytest tests/test_project_cockpit_summary.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_project_cockpit_summary.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Ignore Stale Active Context In Project Cockpit

Change type:

```text
access-control behavior change
project cockpit hardening
regression-test addition
```

Decision:

Project Cockpit now treats a saved active context as absent when the current
non-DBA user no longer has a grant for its project. In that case the summary
returns `needs_context`, clears the active-context payload, omits setup status
and recent records, and disables contextual job/evidence actions.

Reason:

Active context can become stale after grants change. The Cockpit must not keep
exposing project setup status, recent records, or project identifiers merely
because an old context row remains stored for the user.

Validation:

```bash
pytest tests/test_project_cockpit_summary.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_project_cockpit_summary.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Disable Contextual Cockpit Actions Until Active Scope Exists

Change type:

```text
backend contract refinement
project cockpit flow hardening
regression-test update
```

Decision:

Project Cockpit now marks `view_jobs` and `view_evidence` actions as disabled
with `ACTIVE_CONTEXT_REQUIRED` until an active project and environment are
selected. The `set_active_context` action remains available so the Cockpit can
continue acting as the context selector.

Reason:

Cockpit is a context selector and accelerator launcher. Jobs and Evidence Hub
are contextual operational surfaces, so the backend action contract should not
present them as ready before there is a usable active scope.

Validation:

```bash
pytest tests/test_project_cockpit_summary.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_project_cockpit_summary.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Scope Project Cockpit Recent Records To Active Context

Change type:

```text
access-control behavior change
project cockpit hardening
regression-test addition
```

Decision:

Project Cockpit summary now limits recent jobs, artifacts, and evidence for
non-DBA users to the active project, environment, and allowed domain set. DBA
users keep project-level summary visibility for the selected active project.

Reason:

Project Cockpit is the context selector and project-info hub. Its recent record
surface must not leak another environment/domain inside the same project, even
when broad project filtering would look superficially correct.

Validation:

```bash
pytest tests/test_project_cockpit_summary.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_project_cockpit_summary.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Reject Mixed-Scope Evidence Hub Archive Packages

Change type:

```text
scope-integrity behavior change
evidence hub hardening
regression-test addition
```

Decision:

Evidence Hub archive package creation now rejects selected evidence sets that
do not share the same project, profile, environment, domain, visibility, and
access-policy scope. Mixed-scope requests return
`400 EVIDENCE_ARCHIVE_SCOPE_MISMATCH` before any archive artifact, manifest,
evidence, audit, or event record is created.

Reason:

Archive packages are operational records. Creating one archive from multiple
client/domain or environment scopes would either erase the scope or require an
ambiguous composite scope, both of which weaken segregation and auditability.

Validation:

```bash
pytest tests/test_evidence_hub_index.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_evidence_hub_index.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Preserve Scope On Evidence Hub Archive Packages

Change type:

```text
scope-integrity behavior change
evidence hub hardening
regression-test update
```

Decision:

Evidence Hub archive package creation now derives a common scope from the
selected evidence and applies it to the generated archive artifact, archive
manifest, archive evidence, audit metadata, and domain event. When all selected
evidence shares project, profile, environment, domain, visibility, and access
policy, the archive records inherit those values.

Reason:

Evidence Hub archive packages are themselves operational records. If scoped
evidence is packaged into unscoped archive records, later reads, downloads, and
audit/event trails can bypass the segregation model or lose the context needed
for evidence review.

Validation:

```bash
pytest tests/test_evidence_hub_index.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_evidence_hub_index.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Scope Evidence Hub Reads And Downloads To Active Context

Change type:

```text
access-control behavior change
evidence hub hardening
regression-test addition
```

Decision:

Evidence Hub list, detail, archive-package input selection, and artifact
download now apply active-context visibility for non-DBA users. Evidence outside
the active project, environment, or allowed domain set is excluded from lists
and archive inputs. Direct evidence detail returns `403 EVIDENCE_FORBIDDEN`, and
artifact download returns `403 ARTIFACT_FORBIDDEN` when the linked client-safe
evidence is outside the active context. DBA users retain global visibility.

Reason:

Platform records and jobs are now scope-validated, but Evidence Hub was still a
direct read/download surface. Evidence and artifact payloads must not bypass
the client/domain and environment segregation enforced elsewhere.

Validation:

```bash
pytest tests/test_evidence_hub_index.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_evidence_hub_index.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Restrict Job Creation To Active Context For Non-DBA Users

Change type:

```text
access-control behavior change
platform job hardening
regression-test addition
```

Decision:

Non-DBA users can now create platform jobs only inside their active project,
environment, and allowed domain set. Job creation outside that active context,
including hidden projects, cross-domain jobs, and unscoped jobs, returns
`403 JOB_FORBIDDEN`. DBA users keep global job creation authority.

Reason:

Job reads and actions were active-context scoped, but job creation still could
persist records into another client/domain or environment if the caller knew
valid IDs. Creation must follow the same boundary as job visibility.

Validation:

```bash
pytest tests/test_operational_metadata.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_metadata.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Scope Job Reads And Actions To Active Context

Change type:

```text
access-control behavior change
platform job hardening
regression-test addition
```

Decision:

Non-DBA users now see and operate only on platform jobs that match their active
project, environment, and allowed domain set. Job list filtering applies this
active-context boundary, and job detail, events, run, and cancel endpoints
return `403 JOB_FORBIDDEN` when a job exists outside the user's active context.
DBA users keep global job visibility and actions.

Reason:

Job creation already validates operational scope, but direct job reads and
actions could still expose or manipulate jobs from another client/domain or
environment. Jobs emit evidence-like events and audit metadata, so they must
follow the same segregation boundary as operational records.

Validation:

```bash
pytest tests/test_operational_metadata.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_metadata.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Validate Job Operational Scope Before Creation

Change type:

```text
scope-integrity behavior change
platform job hardening
regression-test addition
```

Decision:

`POST /api/v1/platform/jobs` now validates `project_id`, `profile_id`, and
`environment_id` with the same operational-scope rules used by platform
artifact, manifest, and evidence records. Jobs may be global/public only when
they do not provide profile or environment scope; otherwise the project must
exist, and profile/environment must belong to it.

Reason:

Jobs emit audit logs and job events that become operational evidence. Allowing
jobs to carry orphaned or cross-project profile/environment IDs would weaken
the same segregation guarantees being established for artifacts and evidence.

Validation:

```bash
pytest tests/test_operational_metadata.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_metadata.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Validate Platform Record Operational Scope

Change type:

```text
scope-integrity behavior change
platform metadata hardening
regression-test addition
```

Decision:

Platform artifact, manifest, and evidence creation now validate the effective
operational scope before persistence. If `profile_id` or `environment_id` is
provided, `project_id` is required. The referenced project, profile, and
environment must exist, and profile/environment must belong to the selected
project. Evidence validates the inherited effective scope from artifact or
manifest when explicit values are omitted.

Reason:

Access-policy binding validation depends on trustworthy record scope. Allowing
profile/environment IDs from another project would corrupt evidence inheritance
and weaken the client/domain and environment segregation foundation.

Validation:

```bash
pytest tests/test_operational_metadata.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_metadata.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Validate Access Policy Binding On Platform Records

Change type:

```text
access-control behavior change
settings policy-binding foundation
regression-test addition
```

Decision:

Platform artifact, manifest, and evidence creation now validate
`access_policy_id` before persisting it. The referenced policy must exist and
must match the operational record's effective `project_id`, `visibility`, and
`domain_name`. Evidence validates the inherited effective scope when policy,
visibility, project, or domain are inherited from an artifact or manifest.

Reason:

Settings can author access policies, but operational records must not bind to
arbitrary policy IDs or policies from another project/domain/visibility scope.
This is the backend foundation for later UI policy-binding controls.

Validation:

```bash
pytest tests/test_operational_metadata.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_metadata.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Gate Project Setup Status By Visible Project Scope

Change type:

```text
access-control behavior change
settings read-contract hardening
regression-test addition
```

Decision:

`GET /api/v1/platform/projects/{project_id}/setup-status` now requires the
requested project to be visible to the current user. Non-DBA users receive
`403 PROJECT_SETUP_STATUS_FORBIDDEN` for existing projects outside their
grants, while missing projects still return `404 PROJECT_NOT_FOUND`. DBA users
retain global status visibility.

Reason:

Project setup status exposes project names and profile/environment readiness.
Even though selectors and active-context selection are now scoped, direct URL
access to setup status must follow the same visibility boundary.

Validation:

```bash
pytest tests/test_operational_context.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_context.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Protect Active Context Selection With Project Grants

Change type:

```text
access-control behavior change
context-selection hardening
regression-test addition
```

Decision:

`POST /api/v1/platform/active-context` now requires non-DBA users to select
only projects visible through their grants. The endpoint also validates that a
selected profile and environment belong to the selected project before
persisting the active context. Clearing context remains allowed, and DBA users
retain global context selection.

Reason:

Active context drives operational visibility, effective capabilities,
navigation, and Settings setup authority. Letting a user select an ungranted
project or mismatched profile/environment would bypass selector filtering and
could make later module checks reason from an invalid scope.

Validation:

```bash
pytest tests/test_operational_context.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_context.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Scope Settings Access Model Payload By Setup Authority

Change type:

```text
access-control behavior change
settings access-model refinement
regression-test addition
```

Decision:

`/api/v1/platform/settings/access-model` now separates operational visibility
from setup-authoring visibility. Non-DBA users without setup authority receive
only their own user record, their own grants in the active project, the roles
attached to those grants, no global capability catalog, and no access-policy
catalog. Users with Settings setup capabilities keep the broader lists needed
for their granted authoring actions, and DBA users retain global visibility.

Reason:

The Settings UI needs role, user, capability, grant, and policy lists for
authoring, but ordinary scoped users should not receive a directory of other
users, hidden roles, global capabilities, or project policy metadata. Read
contracts must follow the same least-visibility model as the write actions.

Validation:

```bash
pytest tests/test_operational_context.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_context.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Restrict Settings Setup Selectors To Granted Projects

Change type:

```text
access-control behavior change
settings setup contract refinement
regression-test addition
```

Decision:

Settings setup selector APIs now limit non-DBA users to the projects granted to
them. Workspace lists are derived from those visible projects, and profile plus
environment lists return rows only for visible projects. Users without project
grants receive empty selector results. DBA users keep full setup visibility.

Reason:

The Settings authority panel already constrained setup actions, but broad
selector lists could still expose project/profile/environment names outside the
user's allowed scope. Setup selection must follow the same client/domain and
environment segregation model as operational records.

Validation:

```bash
pytest tests/test_operational_context.py -q
```

Impacted docs and tests:

- `docs/agent/HANDOFF.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `tests/test_operational_context.py`

Status:

Implemented and covered by targeted backend regression tests.

## 2026-05-27: Add Settings Scope Authority Contract, Visibility, And UI Panel

Change type:

```text
backend contract change
frontend contract integration
settings completion gate
test coverage change
```

Decision:

Settings now exposes `/api/v1/platform/settings/scope-authority`, a
backend-owned summary for workspace/project/profile/environment setup, active
context state, blocked reasons, setup visibility, and available actions. The
contract distinguishes `SCOPED`, `PROJECT`, and `GLOBAL` setup visibility:
normal users get scoped/read-only setup visibility, project setup admins get
project-level role/grant/access-policy authoring visibility through Settings
capabilities, and `DBA` users keep global setup authority.

The Settings UI consumes that contract in a top-level scope authority panel
with setup counts, active context, blockers, setup visibility, and action
availability without recreating Admin Console logic in the frontend.

Reason:

Settings is the current UI owner for client/domain, environment, profile, user,
role, grant, and access-policy setup. The UI needs a compact contract that says
what is ready, what is blocked, and which setup action should be presented.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
pytest tests/test_operational_scope.py tests/test_operational_metadata.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm test -- src/app/App.test.tsx
npm run build
```

## 2026-05-27: Add Settings Role And Grant Authoring Contracts

Change type:

```text
backend contract change
frontend contract integration
settings completion gate
test coverage change
```

Decision:

Settings now exposes `/api/v1/platform/settings/access-model` plus mutation
contracts for `/api/v1/platform/roles` and `/api/v1/platform/grants`.
Role creation requires `settings.roles.manage` or `DBA`; grant assignment
requires `settings.grants.manage` or `DBA`, and non-DBA grants are limited to
the active project. The Settings UI now renders role and grant authoring forms
from the backend access model.

Reason:

The Settings module must own role and grant setup in the current UI phase. The
previous scope-authority contract showed whether actions were allowed, but
there was no backend mutation path or visible authoring surface for the user to
complete the flow.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
python -m py_compile src/otm_workbench/platform/routes.py
```

## 2026-05-27: Add Settings Access Policy Authoring

Change type:

```text
backend contract change
model contract change
frontend contract integration
settings completion gate
test coverage change
```

Decision:

Settings now has a first-class `AccessPolicy` persistence model and exposes
`POST /api/v1/platform/access-policies`. The existing Settings access model now
returns access policies alongside roles, capabilities, and grants. Policy
creation requires `settings.access_policies.manage` or `DBA`; non-DBA users can
create policies only for their active project. The Settings UI renders a
first-pass access-policy form and policy list from that backend contract.

Reason:

Operational records already carry `access_policy_id`, but Settings did not yet
own a policy authoring contract. This created an incomplete flow between
scope-authority actions and the data segregation model.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
python -m py_compile src/otm_workbench/platform/routes.py
```

## 2026-05-27: Add Settings User Authoring And Grant User Selection

Change type:

```text
backend contract change
frontend contract integration
settings completion gate
test coverage change
```

Decision:

Settings now exposes user setup through `POST /api/v1/platform/users`, guarded
by `settings.users.manage` or `DBA`. The Settings access model now returns
users without password/hash fields, and scope authority includes
`can_manage_users`. The Settings UI renders a first-pass user creation form and
uses a user selector for grant assignment instead of requiring raw `user_id`
entry.

Reason:

Role and grant authoring was functional but still forced users to know internal
user IDs. Settings owns user setup in the current UI phase, so the grant flow
needs a backend-owned user list and a controlled creation path.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
python -m py_compile src/otm_workbench/platform/routes.py
```

## 2026-05-27: Add Domain And Environment Scoped Grants

Change type:

```text
backend behavior change
model contract change
frontend contract integration
settings completion gate
test coverage change
```

Decision:

Settings grants now support optional `environment_id` and `domain_name`.
Effective capabilities and backend navigation honor those fields: a scoped
grant only applies when the user's active project, environment, and domain
match the grant. Existing project-level grants with null environment/domain
remain valid for compatibility. The Settings UI now exposes grant environment
and domain fields and renders the grant domain in the grant list.

Reason:

Client/domain and environment segregation cannot rely on project-level grants
alone. Settings needs to express whether a role applies broadly to a project or
only to a specific OTM domain/environment context.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
python -m py_compile src/otm_workbench/platform/routes.py src/otm_workbench/platform/navigation.py
```

## 2026-05-27: Delegate Profile And Environment Authoring Through Settings Authority

Change type:

```text
backend behavior change
frontend authority alignment
settings completion gate
test coverage change
```

Decision:

Profile and environment creation no longer require global admin only. They now
accept authenticated users when Settings authority grants
`settings.project.manage` for the active project/environment/domain context.
Scoped grants are honored, so a project setup admin for `OTM1` cannot use the
same authority from `OTM2`. The Settings UI now disables setup authoring buttons
from the backend setup visibility contract instead of only relying on local
entity counts.

Reason:

Settings scope authority already advertised project-level profile/environment
authoring. Keeping the backend endpoints admin-only made the UI contract
misleading and prevented project setup admins from completing setup.

Validation:

```bash
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
python -m py_compile src/otm_workbench/platform/routes.py
```

## 2026-05-27: Scope Order Release Templates And Batches

Change type:

```text
backend behavior change
scope enforcement change
model contract change
test coverage change
```

Decision:

Order Release templates and batches now carry project, environment, profile,
and domain scope. Seeded backend templates are `PUBLIC`; user-authored
templates and template versions inherit the active operational context. Template
list, template version creation, batch creation, batch list/detail, XML preview,
XML artifact generation, artifact list/download, and submit guard routes
resolve the template or batch through active context before returning or acting
on data.

Batch rows inherit access through the parent batch. Generated XML artifacts and
evidence inherit the batch scope.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all batch domains inside the active project
and environment. Out-of-scope batches return 404.

Reason:

Order Release templates can encode client/domain-specific authoring contracts,
and batches contain operational order data and generated XML evidence. Both
must be isolated by client/domain and environment before module completion work
continues, while backend seed templates remain shareable public contracts.

Validation:

```bash
pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_jobs.py tests/test_order_release_generator_submit_guard.py -q
pytest tests/test_operational_scope.py tests/test_operational_context.py -q
```

## 2026-05-27: Scope Integration Systems And Endpoints

Change type:

```text
backend behavior change
scope enforcement change
model contract change
test coverage change
```

Decision:

Integration systems now carry project, environment, profile, and domain scope.
System creation inherits the active operational context. System list and
endpoint create/list routes resolve the parent system through active context
before returning or mutating data.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all system domains inside the active project
and environment. Out-of-scope systems return 404 for endpoint operations.

Reason:

Systems and endpoints describe client/domain-specific integration metadata and
must not be visible or attachable across environments or private domains.

Validation:

```bash
pytest tests/test_integration_mapping_systems.py tests/test_integration_mapping_definitions.py tests/test_integration_mapping_mappings.py -q
pytest tests/test_operational_scope.py tests/test_operational_context.py -q
```

## 2026-05-27: Start Integration Definition Access Filtering

Change type:

```text
backend behavior change
scope enforcement change
model contract change
test coverage change
```

Decision:

Integration definitions now carry project, environment, profile, and domain
scope. Definition creation inherits the active operational context. Definition
list/detail/validate/preview/spec/artifact routes, payload artifact and schema
document routes, and definition-owned mappings, loops, joins, join bindings,
lookups, and response handlers resolve the parent definition through active
context before returning or mutating data.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all definition domains inside the active
project and environment. Out-of-scope definitions and child objects return 404.

Reason:

Integration Mapping can contain payload samples, generated specs, schema trees,
and mapping rules that are client/domain-specific. Parent definition scoping
must be enforced before later endpoint/system and executable integration
behavior can be safely exposed.

Validation:

```bash
pytest tests/test_integration_mapping_definitions.py tests/test_integration_mapping_payload_artifacts.py tests/test_integration_mapping_schema_tree.py tests/test_integration_mapping_schema_persistence.py tests/test_integration_mapping_mappings.py -q
pytest tests/test_integration_mapping_loops.py tests/test_integration_mapping_joins.py tests/test_integration_mapping_join_bindings.py tests/test_integration_mapping_lookups.py tests/test_integration_mapping_response_handlers.py -q
pytest tests/test_integration_mapping_spec_generator.py tests/test_integration_mapping_artifacts.py tests/test_integration_mapping_validation.py -q
pytest tests/test_operational_scope.py tests/test_operational_context.py -q
```

## 2026-05-27: Start Master Data Batch Access Filtering

Change type:

```text
backend behavior change
scope enforcement change
model contract change
test coverage change
```

Decision:

Master Data batches now carry project, environment, profile, and domain scope.
Workbook-editor and workbook-upload batch creation inherit the active
operational context. Batch list, summary, detail, artifacts, output records,
CSV files, OTM import readiness/guard, artifact download, relationship
validation, mapping, output build, CSV build, and CSV package export resolve
the batch through active context before returning or mutating data.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all batch domains inside the active project
and environment. Out-of-scope batches return 404.

Reason:

Master Data is a parent workflow for downstream Load Plan packages and must
carry the same explicit client/domain and environment contract before later
module delivery can safely rely on its batches.

Validation:

```bash
pytest tests/test_master_data_templates.py -q
```

## 2026-05-27: Start Assets Route Access Filtering

Change type:

```text
backend behavior change
scope enforcement change
test coverage change
```

Decision:

Assets list, detail, update, archive, link create/list, version upload/list,
and current-version download now resolve the asset through the active
operational context before returning or mutating asset data.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all asset domains inside the active project
and environment. Out-of-scope assets return 404.

Reason:

Asset records already carried project/environment/domain/access-policy metadata,
but route reads and actions still used unscoped `Asset` queries. Assets is the
next module lock after Load Plan because its parent record already has the
scope fields needed by the shared `apply_operational_scope` helper.

Validation:

```bash
pytest tests/test_assets_library_assets.py -q
```

## 2026-05-27: Start Load Plan Package Access Filtering

Change type:

```text
backend behavior change
scope enforcement change
model contract change
test coverage change
```

Decision:

Load Plan packages now carry `domain_name` alongside project, environment, and
profile scope. Package list, summary, detail, intake from Rates, and primary
package actions resolve records through the active operational context before
returning or mutating package data.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all package domains inside the active project
and environment. Out-of-scope packages and source Rate batches return 404.

Reason:

Load Plan already inherited project/environment/domain metadata into generated
artifacts and evidence, but the package route surface still exposed package
records without active-context filtering. Package-level scoping is the parent
lock required before hardening child read models such as sequence snapshots,
CSVUTIL builds, ZIP analyses, readiness, handoff, and review queue lists.

Validation:

```bash
pytest tests/test_load_plan_package_intake.py -q
```

Follow-up lock:

Load Plan child read models now also enforce active-context package scope for:

- ZIP analysis list/detail;
- CSVUTIL build list/detail;
- sequence snapshot list/detail/latest;
- cutover checklist detail and checklist-derived actions;
- cutover readiness list/detail/latest/export;
- readiness export list/detail;
- cutover handoff list/detail;
- review queue generation/list/detail/decision.

Validation:

```bash
pytest tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_sequence_blockers.py tests/test_load_plan_cutover_checklist.py tests/test_load_plan_cutover_readiness.py tests/test_load_plan_readiness_export.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py -q
```

## 2026-05-27: Start Rates Route Access Filtering

Change type:

```text
backend behavior change
scope enforcement change
test coverage change
```

Decision:

Rates batch list, summary, detail, readiness, approval, table intake,
validation, issues, CSV preview, CSV export, artifact, download, and evidence
routes now resolve batches through the active operational context before
returning or mutating a batch.

Normal users are limited to the active project, environment, and domain.
`DBA`/all-domain context can see all domains inside the active project and
environment. Out-of-scope batches return the same 404 contract as missing
batches.

Reason:

The To-Be adaptation requires every operational record to carry and enforce
client/domain and environment scope, not only inherit that metadata on generated
artifacts. Rates is the first module-level route filter lock because its CSV
export inheritance lock already exists.

Validation:

```bash
pytest tests/test_rates_batches.py tests/test_rates_summary.py -q
```

## 2026-05-27: Promote Complete Solution Mockup To Active To-Be Source

Change type:

```text
scope change
roadmap change
delivery pipeline change
validation strategy change
documentation change
feature boundary clarification
```

Decision:

Use `OTM Workbench - Complete Solution Mockup` as the active To-Be visual
source for the next solution-alignment and implementation-planning phase.

Active Figma artifact:

```text
OTM Workbench - Complete Solution Mockup
file-key: 7AkORIWrjmaOiBBA6cMOj9
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

The mockup now contains seven validated deep-flow boards:

- `10 / Rates Studio Deep Flow`;
- `11 / Assets Library Deep Flow`;
- `12 / Load Plan Deep Flow`;
- `13 / Order Release Deep Flow`;
- `14 / Integration Mapping Deep Flow`;
- `15 / Configuration Settings Deep Flow`;
- `16 / Cockpit v3 Deep Flow`.

Validation result:

```text
allPass: true
112 screen cards
0 card overlaps
0 text overflow
16 primary + 16 secondary buttons per board
consistent 34px grid spacing
IBM Plex Sans visual grammar
```

Reason:

The user clarified that the correct target is the Complete Solution Mockup, not
the earlier `Consolidated Scope Wireframes` file. The new deep-flow boards
resolve the previous audit gap where most modules had only macro-board
coverage.

Impacted docs:

- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`
- `docs/otm-workbench/README.md`

Status:

Accepted for To-Be planning. Cleanup, source-code removal, fixture generation,
Linear updates, GitHub PRs, and implementation remain separate delivery slices.

## 2026-05-27: Approve To-Be Implementation Order

Change type:

```text
roadmap change
delivery pipeline change
priority change
validation strategy change
```

Decision:

Use this implementation sequence:

```text
frontend cleanup/navigation pruning
-> client/domain and environment segregation
-> Settings
-> Cockpit
-> Rates
-> Assets
-> Master Data
-> Integration
-> Order Release
```

Load Plan remains in the active UI phase and must be preserved as a cutover,
CSVUTIL, package, and handoff dependency, but it is not the next focused module
after Cockpit unless the user reprioritizes it.

Reason:

The user wants to remove or hide modules that will not be attacked now, then
establish data segregation before finishing Settings and Cockpit. This sequence
protects the access model before operational modules are completed.

Status:

Accepted as planning baseline.

## 2026-05-27: Require Scenario Fixtures Per Module

Change type:

```text
validation strategy change
documentation change
quality bar change
```

Decision:

Every module delivery must plan valid synthetic fixture files and test
scenarios appropriate to the module. Required formats may include `csv`,
`xslt`, `pdf`, `docx`, `md`, `xml`, `json`, large files, ZIPs, and generated
artifact packages.

OTM uncertainty must be validated through the Data Dictionary and official
Oracle documentation before a module can be called complete.

Status:

Accepted as a module delivery gate.

## 2026-05-27: Prune Main Navigation To Current To-Be UI Phase

Change type:

```text
feature boundary change
delivery pipeline change
frontend cleanup change
```

Decision:

Expose only the current To-Be UI phase modules in backend-owned main
navigation:

- Master Data / Data Factory;
- Project Cockpit;
- Rates Studio;
- Load Plan;
- Assets Library;
- Order Release Generator;
- Integration Mapping Studio;
- Settings.

Hide Catalog Core, Evidence Hub, Admin Console, and Developer Tools from the
main navigation. Preserve their backend/internal capabilities for active module
dependencies until later cleanup classification.

Reason:

This is the first safe frontend cleanup step requested by the user: remove
modules that are not being attacked now from the visible UI without destructive
source deletion.

Status:

Implemented as the first cleanup slice. See
`docs/agent/FRONTEND_NAVIGATION_PRUNING_REPORT.md`.

## 2026-05-27: Create FigJam As-Is Solution Diagnostics

Change type:

```text
documentation change
validation strategy change
architecture clarification
cleanup planning change
```

Decision:

Create a FigJam board named `OTM Workbench - Stack As-Is Map` in the
`otm-workbench` team and use it as the current visual diagnostic artifact for
understanding the solution before cleanup or implementation resumes.

FigJam artifact:

```text
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

The board contains:

- stack as-is map;
- UI scope boundary;
- module implementation matrix;
- backend/frontend/database by module;
- operational flow as-is to target;
- cleanup decision flow;
- function status by module;
- core data model overview.

Reason:

The user requested a clear visual view of where the solution is today so the
team can analyze where to cut, alter, or create future work. The diagnostics
make the current backend-rich implementation, active UI phase, excluded
top-level modules, internal dependencies, and cleanup rules explicit.

Impacted docs:

- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/ARCHITECTURE_MAP.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_AS_IS_SOLUTION_DIAGRAMS_REPORT.md`
- `docs/otm-workbench/README.md`

Status:

Accepted as a diagnostic planning artifact. It does not approve cleanup,
archive moves, source-code removal, or reintroduction of excluded modules.

## 2026-05-26: Establish Solon Governance Layer

Change type:

```text
documentation change
delivery pipeline change
project direction change
```

Decision:

Create `docs/agent/` as the short operational governance layer for agents and
humans.

Reason:

The project has strong module and GUI docs, but the active north star, scope,
roadmap, recovery plan, and handoff were spread across multiple locations.

Impacted docs:

- `AGENTS.md`
- `docs/otm-workbench/README.md`
- `docs/agent/*`

Status:

Accepted for this slice.

## 2026-05-26: Use Specs, Not Current UI, For Penpot Wireframes

Change type:

```text
validation strategy change
feature boundary change
```

Decision:

Penpot wireframes will be generated from validated module specs and the module
scope ledger, not by recreating the current UI.

Reason:

The current UI contains historical compromises. Wireframes should express the
target product flow before implementation cleanup begins.

Status:

Accepted.

## 2026-05-26: Cleanup Must Be Reversible First

Change type:

```text
deprecation or replacement change
delivery pipeline change
```

Decision:

No deletion or mass move happens during the governance baseline. Cleanup starts
with inventory and archive candidates. Source code cleanup requires a separate
approved implementation plan.

Reason:

The repo contains useful evidence, old specs, and current local resources. A
destructive cleanup could erase context before replacement docs are validated.

Status:

Accepted.

## 2026-05-26: Protect OTM Resources

Change type:

```text
risk control
```

Decision:

`OTM_RESOURCES/` is protected until the user explicitly asks for changes there.

Reason:

It appears as an untracked local path and may contain Data Dictionary or other
project resources needed for validation.

Status:

Accepted.

## 2026-05-26: Phase 2A Scope Recovery Starts With Master Data And Catalog

Change type:

```text
scope change
validation strategy change
documentation change
```

Decision:

Validate Master Data / Data Factory and Catalog Core first for wireframe brief
preparation.

Reason:

Master Data is the strongest current module redesign and Catalog Core is the
shared source for Data Dictionary, macro-object, schema, and dependency truth
used by other modules.

Impacted docs:

- `docs/agent/MODULE_SCOPE_LEDGER.md`
- `docs/agent/module-scope/MASTER_DATA_DATA_FACTORY_SCOPE_REVIEW.md`
- `docs/agent/module-scope/CATALOG_CORE_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/MASTER_DATA_DATA_FACTORY_WIREFRAME_BRIEF.md`
- `docs/agent/wireframe-briefs/CATALOG_CORE_WIREFRAME_BRIEF.md`

Status:

Accepted for wireframe brief preparation. Cleanup and implementation still
require user approval after Penpot/mockup review.

## 2026-05-26: Complete Documentation For All Modules Before Penpot

Change type:

```text
scope change
delivery pipeline change
documentation change
validation strategy change
```

Decision:

Finish scope reviews and Michelangelo wireframe briefs for every module before
creating Penpot wireframes.

Reason:

This prevents the Penpot phase from becoming a partial redesign based on only
Master Data and Catalog. Every module now has a validated documentation input
for visual design review.

Impacted docs:

- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/MODULE_SCOPE_LEDGER.md`
- `docs/agent/module-scope/*.md`
- `docs/agent/wireframe-briefs/*.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`

Status:

Accepted for documentation. Penpot, cleanup, and implementation remain gated by
user approval.

## 2026-05-26: Include Login And Logout In Shell Wireframes

Change type:

```text
scope change
validation strategy change
documentation change
```

Decision:

Add login, invalid-login, logout-confirmed/session-ended, and signed-out
recovery states to the Shell / Project Cockpit Penpot scope.

Reason:

Authentication and session recovery are part of the shell trust boundary. They
also directly address the known post-sign-out navigation confusion risk.

Impacted docs:

- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`

Status:

Accepted for wireframe planning.

## 2026-05-26: Approve Initial Penpot Wireframe Order

Change type:

```text
delivery pipeline change
priority change
documentation change
```

Decision:

Use this initial Penpot wireframe order:

```text
Project Cockpit -> Master Data -> Coordinate Quality -> Rates -> Load Plan ->
Integration Mapping -> Assets -> Catalog Core -> Evidence Hub -> Order Release
-> Admin -> Dev Tools
```

Reason:

The order starts with shell/session trust and the core Master Data workflow,
then follows adjacent operational modules before returning to shared Catalog
and evidence/admin/technical surfaces.

Impacted docs:

- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/HANDOFF.md`

Status:

Accepted for wireframe planning. Coordinate Quality remains Master Data /
Quality Tools scope, listed separately only for design sequencing.

## 2026-05-26: Prepare Local Penpot Build Packet When Connector Is Blocked

Change type:

```text
documentation change
delivery pipeline change
validation strategy change
```

Decision:

When the Penpot connector cannot complete its required overview step, create a
local Penpot-ready build packet instead of writing to the design file blindly.

Reason:

The Penpot `high_level_overview` call failed twice with a transport
deserialization error. The build packet preserves the approved visual sequence
and frame definitions while keeping the actual Penpot file untouched.

Impacted docs:

- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_PENPOT_BUILD_SPEC.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_WIREFRAME_BLUEPRINT.json`

Status:

Accepted as a temporary fallback for Project Cockpit. Retry direct Penpot
creation before starting the next module board.

Update:

The Penpot endpoint was validated manually through JSON-RPC. The standard
`mcp__penpot__` wrapper still fails, but the underlying Penpot MCP server,
target file, target page, `high_level_overview`, and `execute_code` are working.
Proceed with the validated JSON-RPC path until the wrapper recovers.

## 2026-05-26: Simplify Project Cockpit To Context And Accelerators

Change type:

```text
scope change
project north star change
feature boundary change
validation strategy change
```

Decision:

Project Cockpit v1 is superseded. The Cockpit should not control the whole
project through readiness, blockers, workstreams, jobs, activity, or global
action review. It should provide login/logout/session safety, active
client/domain and environment context, Public View, accelerator launch, and
project information.

Reason:

OTM Workbench is intended to group accelerators that can be used at any point
in a project. It should not force module order or project phase gates. The
stronger invariant is data separation by client/domain, environment, and
visibility/access policy.

Impacted docs:

- `docs/agent/PROJECT_NORTH_STAR.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_WIREFRAME_BLUEPRINT.json`

Status:

Accepted by the user for v2 Penpot creation.

## 2026-05-26: Create Project Cockpit v2 As Separate Penpot Page

Change type:

- deprecation/replacement change;
- documentation change;
- validation strategy change.

Decision:

Keep the Project Cockpit v1 Penpot page as a superseded reference and create
the simplified Cockpit v2 in a separate page:

```text
01B Shell Context and Accelerator Cockpit v2
```

Reason:

The v1 boards provide useful connector evidence but model too much project
control. A separate v2 page avoids mixing the accepted simplified direction with
the earlier over-scoped model.

Impacted docs:

- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_PENPOT_CREATION_REPORT.md`

Status:

Created in Penpot and ready for user/Michelangelo visual review.

## 2026-05-27: Accept Rates For Current Delivery Cycle

Change type:

- module acceptance decision;
- delivery sequencing decision.

Decision:

Rates is accepted for the current delivery cycle after route-level recovery and
deep-flow completion. The active module sequence can move to Assets.

Reason:

Rates now covers the current-cycle route family from hub through library,
creation, batch overview, staging, issues, table detail, CSV preview, export
review, approval review, artifacts, evidence, and Load Plan handoff. Remaining
items are enhancements rather than blockers for the current cycle.

Backlog retained:

- backend-owned advanced search operators and pagination;
- row edit/delete and deeper row detail;
- Data Dictionary metadata on table detail;
- expanded out-of-order browser QA;
- optional dedicated eligibility endpoints for export/handoff.

Validation:

- `docs/agent/RATES_ACCEPTANCE_CHECKLIST_2026-05-27.md`
- `docs/agent/VALIDATION_REPORT.md`

Status:

Accepted for current cycle. Next active module: Assets.

## 2026-05-27: Plan Context Segregation Before Schema Changes

Change type:

- implementation planning;
- access-control boundary clarification;
- test strategy update.

Decision:

Create a dedicated context segregation foundation plan before applying database
or query changes. The plan keeps shared technical metadata global, requires
explicit project/client-domain/environment scope for operational records, and
preserves Public View as a separate shared scope.

Reason:

The codebase already has active context and partial module scope support, but
operational models are uneven. Rates and much of Load Plan already carry
project/environment/domain context, while Integration, Order Release, Master
Data, and shared artifact/evidence records still need retrofit. A blanket
migration would risk either data leaks or duplicated technical catalog data.

Impacted docs:

- `docs/agent/TASK_CONTRACT_CONTEXT_SEGREGATION_FOUNDATION.md`
- `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/DOCUMENT_INVENTORY.md`

Status:

Planning slice complete. The first implementation slice added behavior-lock
tests and a reusable backend scoping utility in
`src/otm_workbench/platform/scoping.py`.

Follow-up:

The model classification ledger was added in
`docs/agent/CONTEXT_SEGREGATION_MODEL_LEDGER.md`. It marks shared Oracle
technical metadata as global, operational parent records as private or
public-capable, and child tables as parent-scoped before migrations.

## 2026-05-27: Add Initial Shared Artifact And Asset Scope Fields

Change type:

- backend contract change;
- schema model change;
- test coverage change.

Decision:

Add initial scope metadata to shared `Artifact`, `Manifest`, `Evidence`, and
`Asset` models. Platform artifact and manifest creation now accept
project/profile/environment/domain/visibility/access-policy metadata, platform
evidence creation inherits scope from the linked artifact or manifest when the
payload omits explicit scope, and Assets create/serialize includes
`domain_name` and `access_policy_id`.

Reason:

Artifacts, manifests, evidence, and assets are shared across modules. They must
carry explicit scope before Settings, Cockpit, Rates, Assets, Master Data,
Integration, Order Release, and Load Plan can safely enforce domain and
environment segregation.

Impacted files:

- `src/otm_workbench/models.py`
- `src/otm_workbench/platform/routes.py`
- `src/otm_workbench/evidence_hub/routes.py`
- `src/otm_workbench/modules/assets/routes.py`
- `src/otm_workbench/modules/assets/assets.py`
- `tests/test_operational_metadata.py`
- `tests/test_assets_library_assets.py`

Status:

Initial shared scope fields are implemented and tested. Module-specific
artifact generators still need inheritance tests in their own retrofit slices.

Follow-up implementation:

Rates CSV export now creates artifact, manifest, and evidence records with
scope inherited from the `RateBatch`. Platform artifact/evidence creation also
normalizes `visibility=PUBLIC` to explicit `domain_name=PUBLIC`, including
direct public evidence records without a linked artifact.

## 2026-05-27: Add Load Plan CSVUTIL Scope Inheritance

Change type:

- backend contract hardening;
- test coverage change.

Decision:

Load Plan CSVUTIL build now creates CTL/CL artifacts, manifest, and evidence
with project/profile/environment inherited from the registered
`LoadPlanPackage`, and domain inherited from the package summary.

Reason:

CSVUTIL build artifacts are operational cutover outputs. They must stay inside
the same client/domain and environment scope as the source Load Plan package.

Impacted files:

- `src/otm_workbench/modules/load_plan/csvutil.py`
- `tests/test_load_plan_csvutil_builder.py`
- `tests/__init__.py`

Status:

CSVUTIL builder scope inheritance is implemented and tested. `tests/__init__.py`
was added so existing cross-file test helpers imported as `tests.*` can be
collected consistently.

## 2026-05-27: Add Load Plan ZIP Analysis Scope Inheritance

Change type:

- backend contract hardening;
- test coverage change.

Decision:

Load Plan ZIP analysis now creates its manifest and evidence with
project/profile/environment inherited from the registered `LoadPlanPackage`,
and domain inherited from the package summary. ZIP analysis audit and domain
event payloads also include the same scope metadata.

Reason:

ZIP analysis results are operational validation evidence and must stay aligned
with the source package scope before route-level access filtering is enforced.

Impacted files:

- `src/otm_workbench/modules/load_plan/zip_analysis.py`
- `tests/test_load_plan_zip_analysis.py`

Status:

ZIP analysis scope inheritance is implemented and tested.

## 2026-05-27: Add Load Plan Cutover Readiness Scope Inheritance

Change type:

- backend contract hardening;
- test coverage change.

Decision:

Load Plan cutover readiness evidence now inherits project/profile/environment
from the registered `LoadPlanPackage`, and domain from the package summary.
Cutover readiness audit and domain event payloads also include the same scope
metadata.

Reason:

Readiness evidence is a cutover decision input. It must remain tied to the same
client/domain and environment as the source package before export and handoff
flows are hardened.

Impacted files:

- `src/otm_workbench/modules/load_plan/readiness.py`
- `tests/test_load_plan_cutover_readiness.py`

Status:

Cutover readiness scope inheritance is implemented and tested.

## 2026-05-27: Add Load Plan Readiness Export Scope Inheritance

Change type:

- backend contract hardening;
- test coverage change.

Decision:

Load Plan readiness export now creates artifact, manifest, and evidence records
with project/profile/environment inherited from the source cutover readiness,
and domain inherited from the readiness summary. Readiness export audit and
domain event payloads also include the same scope metadata.

Reason:

Readiness export packages are operational handoff evidence and must remain in
the same client/domain and environment as the readiness record they export.

Impacted files:

- `src/otm_workbench/modules/load_plan/readiness.py`
- `src/otm_workbench/modules/load_plan/readiness_export.py`
- `tests/test_load_plan_readiness_export.py`

Status:

Readiness export scope inheritance is implemented and tested.

## 2026-05-27: Add Load Plan Cutover Handoff Scope Inheritance

Change type:

- backend contract hardening;
- test coverage change.

Decision:

Load Plan cutover handoff now creates evidence with project/profile/environment
inherited from the registered `LoadPlanPackage`, and domain inherited from the
package summary. Handoff audit and domain event payloads also include the same
scope metadata.

Reason:

The handoff is the terminal operational cutover signal for a package. It must
retain the same client/domain and environment scope as the package and all
upstream readiness evidence.

Impacted files:

- `src/otm_workbench/modules/load_plan/cutover_handoff.py`
- `tests/test_load_plan_cutover_handoff.py`

Status:

Cutover handoff scope inheritance is implemented and tested.

## 2026-05-27: Apply Complete Mockup Visual Grammar Without Scope Expansion

Change type:

- validation strategy change;
- feature boundary clarification;
- documentation change.

Decision:

Update `OTM Workbench - Consolidated Scope Wireframes` with a v2 page named
`Current Scope v2 - Prototype DNA`. The v2 page applies the Complete Solution
Mockup visual/component grammar while keeping the current eight-module UI phase:

- Cockpit;
- Master Data / Data Factory;
- Rates Studio;
- Load Plan / Cutover;
- Integration Mapping Studio;
- Order Release Generator;
- Assets Library;
- Settings.

Reason:

The user explicitly selected `1A,2A,3A`: keep the current scope, keep the
artifact low-fidelity, and use the linked Complete Solution Mockup as the
prototype reference. The update improves density, visual consistency, and
component grammar without reintroducing excluded modules.

Status:

Accepted for the current Figma wireframe pass.

## 2026-05-27: Consolidate Current UI Phase In Figma

Change type:

- scope change;
- roadmap change;
- delivery pipeline change;
- feature boundary change;
- validation strategy change.

Decision:

Use the Figma Pro project as the active visual consolidation target for this
phase and keep only these top-level UI modules:

- Cockpit;
- Master Data / Data Factory;
- Rates Studio;
- Load Plan / Cutover;
- Integration Mapping Studio;
- Order Release Generator;
- Assets Library;
- Settings.

Settings absorbs project creation, client/domain, environment, profile,
user, role, grant, and access-policy setup for the current UI phase. Catalog Core,
Evidence Hub, separate Admin Console / Jobs, Developer Tools, Coordinate
Quality as a top-level module, and generic dashboards stay out of the main UI
for now.

Reason:

The user wants to avoid spending more time on over-broad wireframes and move to
a consolidated Figma direction based on the supplied PDF. Limiting the main UI
keeps the workbench focused on accelerators and configuration needed for the
next implementation phase.

Impacted docs:

- `AGENTS.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_UI_PHASE_CONSOLIDATION_REPORT.md`

Historical Figma artifact:

```text
OTM Workbench - Consolidated Scope Wireframes
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
supporting page: Current Scope v2 - Prototype DNA
```

Status:

Accepted for current UI phase consolidation. Cleanup and implementation remain
gated by user review and approval.

## 2026-05-26: Replace Project Cockpit v2.1 With v3 Single Cockpit

Change type:

- scope change;
- feature boundary change;
- deprecation/replacement change;
- validation strategy change.

Decision:

Project Cockpit v3 is the active target. It removes separate `Client Overview`,
`Public View`, and `Project Info` sidebar/shell routes. The authenticated
Cockpit is one screen with these macro groups:

- Context Selector;
- Project Info;
- Accelerators.

The Context Selector defines Public vs client/domain and environment. Project
Info is available only inside the Cockpit. The sidebar contains Cockpit,
accelerators, Admin, and Dev Tools.

Reason:

User review clarified that the extra v2.1 route boards still made the Cockpit
feel like a routed workflow. The product should stay compact and treat context,
project references, and accelerator launch as parts of one Cockpit surface.

Impacted docs:

- `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`
- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V3_PENPOT_CREATION_REPORT.md`

Penpot cleanup:

- v1 generated boards removed;
- v2.1 generated boards removed;
- old pages renamed as superseded empty pages because the plugin API does not
  expose direct page deletion.

Status:

Created in Penpot and ready for user/Michelangelo visual review.

## 2026-05-26: Revise Project Cockpit v2 To v2.1 Navigation Shell

Change type:

- documentation change;
- validation strategy change;
- feature boundary clarification.

Decision:

Revise the active Project Cockpit Penpot page to v2.1 by adding:

- `SHELLV2-00 Navigation map`;
- route arrows and entry-path notes;
- persistent authenticated sidebar;
- top-right Light/Dark toggle;
- user menu and Logout;
- visible routes from Cockpit to Client Overview, Public View, and Project Info
  Hub.

Reason:

User review showed that the v2 boards did not clearly explain how to reach
`SHELLV2-04`, `SHELLV2-05`, or `SHELLV2-06`, and the authenticated shell was
missing expected navigation/account controls.

Impacted docs:

- `docs/agent/module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md`
- `docs/agent/PENPOT_WIREFRAME_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_WIREFRAME_BLUEPRINT.json`
- `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_PENPOT_CREATION_REPORT.md`

Status:

Created in Penpot and ready for user/Michelangelo visual review.
