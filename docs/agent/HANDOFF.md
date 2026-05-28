# Handoff

**Status:** active
**Date:** 2026-05-27

## 2026-05-27 Assets Links Route Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has a route-level link management screen at
`/assets/:assetId/links`.

What changed:

- `/assets/:assetId/links` renders a relationship editor for one asset;
- existing links render as route-level rows with target label, link type, target
  id, and creator;
- link creation uses the existing backend `POST /assets/{asset_id}/links`
  contract and backend-owned link type classifications;
- the direct route preserves guided target choices for modules, macro objects,
  OTM tables, artifacts, and evidence through the current frontend/backend
  contracts;
- the direct route exposes `Back to Asset` and `Back to Library`;
- browser QA creates a `MODULE` link through the direct route and captures
  `var/qa/assets-links-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset link"` -> 1
  passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 7 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `npm run qa:functional:assets:browser` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8017`;
- frontend: `http://127.0.0.1:5194`;
- database: `var/qa-assets-links-route.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots: `var/qa/assets-links-route.png`,
  `var/qa/assets-version-upload-route.png`, `var/qa/assets-versions-route.png`,
  `var/qa/assets-edit-metadata-route.png`, `var/qa/assets-detail-route.png`.

Recommended next step:
Continue Assets route extraction with classifications and archive review, then
do an Assets acceptance pass against the consolidated spec.

## 2026-05-27 Assets Versions Routes Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has route-level version history and direct version upload
screens.

What changed:

- `/assets/:assetId/versions` renders version history, current-version state,
  guarded current-version download, and return/upload paths;
- `/assets/:assetId/versions/new` renders direct upload for one asset using the
  existing backend version upload contract;
- neither direct versions route renders the temporary Assets Library workflow
  rail;
- the asset detail route's existing `Versions` link now resolves to a real
  route-level screen;
- browser QA uploads through the direct route, visits version history, validates
  live navigation IDs, and captures `var/qa/assets-version-upload-route.png`
  plus `var/qa/assets-versions-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset versions route"`
  -> 1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "uploads an asset version on a direct route"`
  -> 1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 6 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `npm run qa:functional:assets:browser` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8016`;
- frontend: `http://127.0.0.1:5192`;
- database: `var/qa-assets-versions-routes.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots: `var/qa/assets-version-upload-route.png`,
  `var/qa/assets-versions-route.png`, `var/qa/assets-edit-metadata-route.png`,
  `var/qa/assets-detail-route.png`.

Recommended next step:
Continue Assets route extraction with dedicated asset link management, then
classifications and archive review.

## 2026-05-27 Assets Edit Metadata Route Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has a dedicated route-level metadata edit screen at
`/assets/:assetId/edit`.

What changed:

- `/assets/:assetId/edit` renders a metadata-only edit workspace with asset
  name, description, type, category, visibility, scope, sensitivity, module,
  macro object, OTM table, and tags;
- the direct edit route uses the existing backend `PATCH` asset contract;
- the asset detail route now exposes `Edit metadata`;
- the direct edit route exposes `Back to Asset` and `Back to Library`;
- the temporary `/assets/library` workflow remains intact while later slices
  extract versions, links, classifications, and archive review;
- browser QA now visits the direct edit route, saves metadata, verifies fresh
  live navigation IDs, and captures `var/qa/assets-edit-metadata-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "edits asset metadata"`
  -> 1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 4 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `npm run qa:functional:assets:browser` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8015`;
- frontend: `http://127.0.0.1:5191`;
- database: `var/qa-assets-edit-metadata-route.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots: `var/qa/assets-edit-metadata-route.png`,
  `var/qa/assets-detail-route.png`.

Recommended next step:
Continue Assets route extraction with dedicated version upload/history screens,
then link management, classifications, and archive review.

## 2026-05-27 Assets Detail Route Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has the first direct route-level object inspection screen at
`/assets/:assetId`.

What changed:

- `/assets/:assetId` renders asset metadata, version history, linked workbench
  objects, lifecycle state, and visible `Back to Assets` / `Back to Library`
  paths;
- Assets hub rows now expose `Open detail`;
- `/assets/library` continues to host the existing functional workflow bridge;
- Assets creation now inherits missing project/profile/environment/domain scope
  from the active context so newly created assets remain visible to their own
  detail, update, version, link, download, and archive routes;
- the browser QA script now checks live navigation for excluded stale modules
  before proceeding, seeds synthetic artifact/evidence targets when needed, and
  includes the new detail route screenshot step.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"`
  -> 1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 3 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `python -m pytest tests/test_assets_library_assets.py -q` -> 18 passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- command: `npm run qa:functional:assets:browser`;
- backend: `http://127.0.0.1:8014`;
- frontend: `http://127.0.0.1:5190`;
- database: `var/qa-assets-detail-route-2.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshot: `var/qa/assets-detail-route.png`.

Root cause note:
The first browser QA attempt failed on the stale default backend/database at
`http://127.0.0.1:8000`; that database lacked current Assets scope columns. A
fresh runtime then exposed and confirmed the create-scope inheritance bug fixed
in this slice.

Recommended next step:
Continue Assets route extraction with edit metadata, versions, links,
classifications, and archive review screens.

## 2026-05-27 CodeRabbit Governance Update

Status:
Applied.

Scope:
Governance now recognizes CodeRabbit as an optional assistive PR reviewer.
GitHub Actions remains the default CI gate. Solon docs and repository docs
remain the durable source of truth.

Files intentionally changed:

- `.coderabbit.yaml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `AGENTS.md`
- `docs/otm-workbench/governance/CODERABBIT_REVIEW_GOVERNANCE.md`
- `docs/otm-workbench/governance/GITHUB_DELIVERY_GOVERNANCE.md`
- `docs/otm-workbench/README.md`
- `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/PROJECT_BRIEF.md`
- `docs/agent/PROJECT_NORTH_STAR.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- GitHub PR checks for #182 were green before this governance update.
- CodeRabbit official docs were checked for root `.coderabbit.yaml`,
  path filters, and path instructions.

Validation not run:

- CodeRabbit CLI review was not run because the local `coderabbit` command is
  not installed/authenticated in this terminal.

Open risks:

- CodeRabbit can be noisy if made mandatory too early.
- Draft PR review is intentionally disabled in `.coderabbit.yaml`; request a
  manual review or mark a PR ready when a CodeRabbit pass is desired.

Recommended next step:

Install/authenticate CodeRabbit CLI or request CodeRabbit review on PR #182,
then decide whether its findings are useful enough to keep the config as-is.

## 2026-05-27 GitHub Operating Setup Follow-Up

Status:
Applied and pushed as the next GitHub governance step.

Scope:
The GitHub CLI is installed at `C:\Program Files\GitHub CLI\gh.exe`, version
2.92.0, and authenticated as `Mr4ndre4tt4`.

What changed:

- created lightweight GitHub labels:
  `scope`, `frontend`, `backend`, `docs`, `qa`, `governance`, `blocked`,
  `scope-risk`;
- created phase milestones:
  Governance Reset, UI Phase Cleanup, Context Segregation, Settings, Cockpit,
  Rates, Assets, Master Data, Integration, Order Release;
- applied labels and milestones to issues #183 through #187;
- reviewed the first GitHub Actions failures;
- corrected `.github/workflows/ci.yml` so CI runs the current governance/UI
  phase representative suite instead of the full historical suite that still
  depends on local protected `OTM_RESOURCES/` and paused module surfaces;
- after the first correction, removed `tests/test_assets_library_assets.py`
  from the backend CI gate because it indirectly depends on local Data
  Dictionary resources and fails in GitHub's clean runner.

Validation:

- `python -m pytest tests/test_modules_navigation.py tests/test_operational_context.py tests/test_project_cockpit_summary.py tests/test_rates_batches.py tests/test_assets_library_assets.py -q`
  -> 67 passed locally where protected local `OTM_RESOURCES/` exists;
- GitHub CI backend gate narrowed to navigation, operational context, Cockpit
  summary, and Rates batches until an Assets/Data Dictionary CI-safe fixture is
  added;
- `npm test -- src/app/AppFunctionalAssets.test.tsx src/app/AppFunctionalRates.test.tsx src/app/AppFunctionalShell.test.tsx`
  -> 3 files passed, 7 tests passed;
- `npm run build` -> passed with the existing Vite large chunk warning.

Open:
Branch protection is not enabled yet. Keep #183 open until the first corrected
CI run is reviewed and the branch protection decision is recorded.

## 2026-05-27 GitHub Governance Migration

Status:
Applied in docs and repository controls.

Scope:
GitHub Issues, Pull Requests, and Actions are now the active delivery
visibility layer. Linear is historical/paused unless the user explicitly
reactivates it.

What changed:

- added GitHub delivery governance under
  `docs/otm-workbench/governance/GITHUB_DELIVERY_GOVERNANCE.md`;
- added PR and Issue templates under `.github/`;
- added GitHub Actions CI for backend tests, frontend tests, and frontend
  build;
- updated active Solon controls to stop requiring Linear updates for new
  slices;
- kept historical Linear docs and issue references as supporting evidence.

Next agent rule:
For new delivery slices, create/update a GitHub Issue and PR. Do not update
Linear unless the user explicitly reactivates it.

## 2026-05-27 GitHub Recovery Checkpoint

Status:
In progress during this handoff update.

Scope:
The local worktree accumulated a large validated-but-unpushed delivery batch
across governance, context segregation, Settings/Cockpit/Rates completion,
Assets hub/library start, fixtures, and validation docs. The current priority
is to publish a recoverable GitHub checkpoint before starting more feature
work.

Checkpoint rules:

- do not include `OTM_RESOURCES/`;
- split commits by reviewable concern where practical;
- preserve docs, tests, and code together;
- push the current branch after validation and commits;
- keep any uncommitted remainder explicit in the final status.

Validation plan:

- run targeted backend tests covering navigation, context, Cockpit, Rates, and
  Assets;
- run focused frontend functional tests for shell, Rates, and Assets;
- run frontend build if the focused tests pass.

## Current State

The active design target is now the Complete Solution Mockup deep-flow board
set. OTM Workbench remains a local-first accelerator workbench, not a
project-management control system.

Active To-Be Figma file:

```text
OTM Workbench - Complete Solution Mockup
file-key: 7AkORIWrjmaOiBBA6cMOj9
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

Supporting Figma file:

```text
OTM Workbench - Consolidated Scope Wireframes
file-key: zJGLRJCTArRStISGIPQ2DQ
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
supporting page: Current Scope v2 - Prototype DNA
```

Active FigJam diagnostic board:

```text
OTM Workbench - Stack As-Is Map
file-key: 4oR1pKe0Ia3g5IeJlkLnh2
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

The FigJam board contains:

- `OTM Workbench - Stack As-Is Map`
- `OTM Workbench - UI Scope Boundary`
- `OTM Workbench - Module Implementation Matrix`
- `OTM Workbench - Backend Frontend DB By Module`
- `OTM Workbench - Operational Flow As-Is To Target`
- `OTM Workbench - Cleanup Decision Flow`
- `OTM Workbench - Function Status By Module`
- `OTM Workbench - Core Data Model Overview`

The active Complete Solution Mockup page contains these To-Be deep-flow boards:

- `10 / Rates Studio Deep Flow`
- `11 / Assets Library Deep Flow`
- `12 / Load Plan Deep Flow`
- `13 / Order Release Deep Flow`
- `14 / Integration Mapping Deep Flow`
- `15 / Configuration Settings Deep Flow`
- `16 / Cockpit v3 Deep Flow`

Final Figma double check passed:

```text
allPass: true
112 screen cards
0 overlaps
0 text overflow
16 primary + 16 secondary buttons per board
consistent 34px grid spacing
```

## Current UI Phase Direction

The main UI carries only:

- Cockpit;
- Master Data / Data Factory;
- Rates Studio;
- Load Plan / Cutover;
- Integration Mapping Studio;
- Order Release Generator;
- Assets Library;
- Settings.

Settings owns project creation, client/domain, environment, profile, user,
role, grant, and access-policy setup for this phase.

Out of the main UI for now:

- Catalog Core as a top-level route;
- Evidence Hub as a top-level route;
- separate Admin Console / Jobs;
- Developer Tools;
- Coordinate Quality as a top-level module;
- generic dashboards, readiness boards, workstream boards, blocker boards,
  activity timelines, and job dashboards.

## Runtime Freshness Guardrail

Incident recorded on 2026-05-27:

A browser screenshot taken during the Assets slice showed excluded sidebar
modules even though the source navigation whitelist and navigation tests were
already correct. The cause was a stale local backend process serving an older
navigation contract. After restarting the backend, live
`/api/v1/platform/navigation` no longer returned the excluded modules for the
demo context.

Before accepting any new browser QA screenshot:

1. confirm the current UI phase module set in `docs/agent/CURRENT_SCOPE.md`;
2. run `pytest tests/test_modules_navigation.py -q` or inspect an equivalent
   navigation guard when code did not change;
3. query the live browser QA backend at `/api/v1/platform/navigation` using the
   same user/session context;
4. compare returned module IDs against current scope and role permissions;
5. restart the backend/dev server or use a fresh port if the API or sidebar
   exposes excluded modules;
6. record backend URL, frontend URL, user context, navigation result, and
   screenshot path in the validation report.

Screenshots showing Catalog Core, Evidence Hub, separate Admin Console / Jobs,
Developer Tools, Coordinate Quality as a top-level module, or generic
dashboards are invalid evidence for the current UI phase unless the user has
explicitly reintroduced that scope.

## Chat Continuity Guardrail

Incident-prevention rule recorded on 2026-05-27:

New chats can lose or compress critical context from the previous session. From
now on, continuation does not rely on conversational memory alone. The durable
workflow is `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`.

New chat intake must rebuild context from:

1. `AGENTS.md`;
2. `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`;
3. latest sections of `docs/agent/HANDOFF.md`;
4. latest sections of `docs/agent/VALIDATION_REPORT.md`;
5. `docs/agent/DECISION_LOG.md`;
6. `docs/agent/RISK_REGISTER.md`;
7. `docs/agent/CURRENT_SCOPE.md`;
8. `docs/agent/DELIVERY_PIPELINE.md`;
9. `git status --short`;
10. relevant diffs for files the new task may touch.

Previous chat exit must leave a concise handoff capsule whenever behavior,
docs, tests, QA evidence, GitHub, or design artifacts changed. Silent partial
work is now considered invalid handoff.

## Prototype Adaptation

The To-Be boards apply the Complete Solution Mockup visual grammar:

- IBM Plex Sans;
- compact desktop density;
- fixed sidebar and top context bar;
- tables, chips, buttons, stage rows, and annotation panels;
- backend-owned action availability and visible blocked reasons.

The scope was not expanded. Catalog Core, Evidence Hub, separate Admin/Jobs,
Developer Tools, and standalone Coordinate Quality remain out of top-level UI.

## Cockpit Direction

The authenticated Cockpit is one screen with three macro groups:

- `Context Selector`: defines Public vs client/domain and environment;
- `Project Info`: URLs, docs, contacts, and secure-vault metadata inside
  Cockpit;
- `Accelerators`: entry cards for the active UI phase modules.

No `Client Overview`, separate `Public View`, or separate `Project Info`
route/sidebar item exists in the current target.

## Previous Penpot Context

Earlier Penpot work remains historical/supporting evidence:

- Project Cockpit v1 and v2.1 generated boards were removed from active Penpot
  pages because they over-scoped the Cockpit.
- Project Cockpit v3 captured the simplified single-cockpit direction before
  the current Figma consolidation.

## Product Invariants

- Every operational record must be scoped by client/domain, environment, and
  visibility/access policy.
- Public scope is selected inside Context Selector.
- Settings owns client/domain, environment, user, role, grant, and permission
  setup for the current UI phase.
- `DBA` has full visibility; normal users operate only inside allowed scopes.
- Project Info may reference useful URLs/docs/contacts and secure-vault
  metadata, but no secret values appear in docs, wireframes, tests, fixtures,
  or screenshots.

## Files Added Or Updated

- `AGENTS.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/TASK_CONTRACT_TO_BE_ALIGNMENT.md`
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_UI_PHASE_CONSOLIDATION_REPORT.md`

## Open Issues

- Frontend route/component inventory still must classify what to keep, hide,
  absorb, alter, archive, remove, or create, but the first navigation pruning
  slice is implemented.
- Client/domain and environment segregation now has a staged implementation
  plan, behavior-lock tests, a reusable backend scoping utility, a model
  classification ledger, initial shared Artifact/Manifest/Evidence/Asset scope
  fields, explicit Public View normalization in platform artifacts/evidence,
  and module-generator inheritance locks in Rates CSV export, Load Plan CSVUTIL
  build, Load Plan ZIP analysis, Load Plan cutover readiness, and Load Plan
  readiness export, and Load Plan cutover handoff. Rates route access filtering
  covers list, summary, detail, readiness, approval, table intake, validation,
  issues, CSV preview/export, artifacts/download, and evidence. Load Plan
  package access filtering has started: packages now carry `domain_name`, and
  package list, summary, detail, intake from Rates, and primary package actions
  are active-context filtered. Load Plan child read-model access filtering now
  covers ZIP analysis, CSVUTIL builds, sequence snapshots, cutover checklists
  and checklist-derived actions, cutover readiness, readiness exports, cutover
  handoff, and review queue. The next implementation slice can return to
  remaining Settings/Cockpit completion gates or start the next module access
  lock. Assets route access filtering has started and covers list, detail,
  update, archive, link create/list, version upload/list, and current-version
  download. Master Data batch access filtering has started: batches now carry
  project/environment/profile/domain scope, workbook-editor and workbook-upload
  creation inherit active context, and the primary batch read/action routes are
  active-context filtered. Integration definition access filtering has started:
  definitions now carry project/environment/profile/domain scope, creation
  inherits active context, and definition-owned payload, schema, mapping, loop,
  join, lookup, response-handler, spec, and artifact routes are active-context
  filtered. Integration systems now also carry project/environment/profile/domain
  scope, creation inherits active context, and system list plus endpoint
  create/list routes are active-context filtered. Order Release access
  filtering has started: seeded templates are `PUBLIC`, user-authored templates
  and batches carry project/environment/profile/domain scope, template and
  batch creation inherit active context, template list/version routes plus batch
  list/detail/XML preview/XML artifact/artifact download/submit guard routes
  are active-context filtered, and generated XML artifacts/evidence inherit
  batch scope. Settings scope authority has started: the backend now exposes
  `/api/v1/platform/settings/scope-authority` with setup counts, active
  context, blocked reasons, setup visibility, and backend-owned available
  actions, and the Settings UI renders that contract in a top-level scope
  authority panel. Settings scope authority now differentiates normal scoped
  users, project setup admins, and `DBA` users before exposing setup actions.
  Settings role/grant authoring has started: `/api/v1/platform/settings/access-model`
  lists roles, capabilities, and grants, `/api/v1/platform/roles` creates roles
  with capabilities, `/api/v1/platform/grants` assigns project roles to users,
  and the Settings UI renders first-pass role and grant forms from that
  contract. Settings access-policy authoring has started: `AccessPolicy` is now
  persisted, `/api/v1/platform/access-policies` creates project/global policies
  according to `settings.access_policies.manage` or `DBA`, and the Settings UI
  renders first-pass policy authoring from the access model. Settings user
  authoring has started: `/api/v1/platform/users` creates users under
  `settings.users.manage` or `DBA`, the access model lists users without
  password/hash fields, and grant authoring now uses a user selector instead of
  raw ID entry. Grants can now be scoped by `environment_id` and `domain_name`;
  effective capabilities and navigation honor those fields while legacy
  project-level grants without environment/domain remain valid. Profile and
  environment authoring now use Settings authority instead of global admin-only
  access, and scoped `settings.project.manage` grants are honored by the
  backend and reflected in disabled/enabled Settings UI controls. Settings
  setup selectors now restrict non-DBA users to granted projects: workspace
  lists are derived from visible projects, while project, profile, and
  environment lists return only granted scope rows. The Settings access-model
  payload is now authority-scoped as well: ordinary scoped users receive only
  their own user/grant/role context and no global capability or policy catalog,
  while setup admins and DBA users retain the broader lists needed for their
  granted actions. Active context selection is now protected by project grants
  for non-DBA users and rejects profile/environment values that do not belong
  to the selected project. Project setup-status reads are also grant-gated, so
  direct URL access cannot expose readiness counts or project names outside the
  visible project scope. Platform artifact, manifest, and evidence creation now
  validates effective project/profile/environment scope before persistence, then
  validates `access_policy_id` bindings against an existing policy with matching
  project, visibility, and domain scope. Platform job creation now uses the
  same operational-scope validation before emitting job records, events, and
  audit metadata. Platform job list/detail/events/run/cancel now restrict
  non-DBA users to jobs matching their active project, environment, and allowed
  domain set. Platform job creation now applies that same active-context
  boundary for non-DBA users, rejecting hidden-project, cross-domain, and
  unscoped job creation. Evidence Hub list/detail/archive input selection and
  artifact download now apply active-context visibility for non-DBA users,
  returning explicit forbidden errors for hidden evidence/artifacts. Evidence
  Hub archive package records now inherit the common project/profile/environment
  domain, visibility, and access-policy scope from the selected evidence, and
  mixed-scope archive requests are rejected before archive records are created.
- Cockpit hardening has started: Project Cockpit recent jobs, artifacts, and
  evidence now respect active project, environment, and allowed domain scope for
  non-DBA users instead of relying on project-only filtering. Contextual
  Cockpit actions for jobs and evidence now stay disabled with
  `ACTIVE_CONTEXT_REQUIRED` until active project/environment scope exists.
  Saved Cockpit active contexts are now ignored when a non-DBA user no longer
  has a grant for the stored project, environment, and domain combination,
  preventing stale or shifted-scope context from exposing setup status or
  recent records.
- Rates hardening has moved beyond read guards: non-DBA users without active
  context now receive an empty batch list and 404 detail responses, and batch
  creation requires active project/environment scope plus matching domain and
  profile boundaries.
- Assets hardening now blocks the no-context read fallback for non-DBA users:
  asset list returns empty and detail/links/versions/download routes return
  not-found when no active project/environment/domain context exists.
- Master Data batch hardening now blocks the no-context fallback for non-DBA
  users: operational batch list/summary/detail/child read routes hide existing
  batches, and workbook-editor/workbook-upload batch creation requires active
  project/environment context.
- Integration hardening now blocks no-context fallback for non-DBA users across
  definitions and systems: list/detail/parent-scoped child routes hide existing
  records, and definition/system creation requires active project/environment
  context.
- Order Release hardening now blocks no-context fallback for non-DBA users
  across operational batches and private templates: public seed templates stay
  visible, private templates/batches are hidden, and template/batch creation
  requires active project/environment context.
- Load Plan hardening now blocks no-context fallback for non-DBA users at the
  package root: package list/detail/summary hide existing records, package
  registration from Rates/Master Data resolves source batches through scoped
  queries, and child workflows remain protected through package scope.
- Cross-project negative coverage is now present across the active operational
  module sequence: Rates, Assets, Master Data, Integration, Order Release, and
  Load Plan all have active-context tests proving records from another project
  are hidden from list/detail/action or representative child routes.
- DBA visibility coverage is present across the same sequence: each module has
  tests proving all-domain visibility inside the active environment while still
  excluding records from other environments.
- Public View coverage remains intentionally narrow: platform
  artifacts/evidence make public scope explicit with `visibility=PUBLIC` and
  `domain_name=PUBLIC`, and Order Release seed templates stay visible as shared
  metadata while private records remain hidden without a valid active context.
  No operational module has been given implicit public/shared visibility.
- Integration Mapping child CRUD/access coverage now includes non-DBA users
  without active context for mapping create/list/detail/delete. Those routes
  resolve through the scoped parent definition and return not-found instead of
  exposing or mutating hidden mappings.
- Master Data action coverage now includes non-DBA users without active context
  for batch validate/map/build-output/build-csv/export-csv-package and
  submit-otm routes. Hidden batches return not-found before any transformation,
  CSV generation, export, or OTM submission work can run.
- Master Data CSV package export now also preserves generated-record scope:
  the ZIP artifact, manifest, and evidence inherit project/profile,
  environment, domain, and `PROJECT` visibility from the source
  `MasterDataBatch`.
- Integration Mapping generated artifacts now preserve source-definition scope:
  payload samples, preview JSON artifacts, and generated markdown specs inherit
  project/profile, environment, domain, and `PROJECT` visibility from the
  `IntegrationDefinition`.
- Load Plan package intake now preserves source-batch scope for both sources:
  Rates intake evidence and Master Data package/intake evidence inherit
  project/profile, environment, domain, and `PROJECT` visibility from the
  source batch.
- Load Plan cutover package flow now preserves package/checklist scope:
  checklist creation/readiness evidence, cutover package export
  artifact/manifest/evidence, and go/no-go evidence inherit project/profile,
  environment, domain, and `PROJECT` visibility from the registered package
  path.
- Order Release XML generation now preserves batch scope: generated XML
  artifacts and evidence inherit project/profile, environment, domain, and
  `PROJECT` visibility from the source `OrderReleaseBatch`.
- Rates approval evidence now preserves batch scope: approval evidence inherits
  project/profile, environment, domain, and `PROJECT` visibility from the
  source `RateBatch`.
- Load Plan sequence snapshot evidence now preserves package scope: generated
  snapshot evidence inherits project/profile, environment, domain, and
  `PROJECT` visibility from the source `LoadPlanPackage`.
- Load Plan review decision evidence now preserves package scope: generated
  decision evidence inherits project/profile/environment from the review item
  and domain from the source `LoadPlanPackage`; audit/event payloads include
  the same scope metadata.
- Master Data published-template workbook generation now marks shared
  template artifacts explicitly with `domain_name=PUBLIC` and
  `visibility=PUBLIC`.
- Task 4 of the context-segregation plan is closed for active UI phase modules:
  generated artifacts/evidence either inherit private operational scope from
  the source record or are explicitly public shared artifacts. Coordinate
  Quality export remains a documented `needs-review` exception because the
  parent batch model has no operational scope fields and the utility is outside
  top-level UI scope for this phase.
- Task 5 of the context-segregation plan is closed: Settings is the setup
  authority for project/client-domain/environment/profile/user/role/grant/
  access-policy setup in the current phase, and the existing
  `AdminConsoleView` component name remains intentionally preserved until a
  deliberate rename slice is approved.
- Task 6 of the context-segregation plan is closed for the active operational
  module sequence: Cockpit, Rates, Assets, Master Data, Integration,
  Order Release, and Load Plan have representative context/route guard coverage
  and targeted validation evidence.
- Load Plan action/update coverage now includes non-DBA users without active
  context for package child creation, checklist item update, sequence snapshot,
  cutover readiness, and cutover handoff routes. These all resolve through the
  scoped package boundary before doing work.
- The active operational sequence now has create/list/detail/update/delete or
  equivalent action coverage for the exposed backend surface. Assets uses
  archive as logical delete; modules without hard-delete endpoints were covered
  through their action routes instead of inventing unsupported CRUD semantics.
- Context segregation foundation tasks 1-8 are now closed for the active UI
  phase. Settings/Cockpit scope authority and operational module guard coverage
  are no longer open items in this plan; future Settings or Cockpit work should
  be handled as module completion slices against the deep-flow boards.
- Project Info secure vault behavior needs a separate security design before
  implementation.
- Cleanup targets are not approved for source deletion yet.
- GitHub delivery updates are deferred until the next implementation or
  approved tracking slice.

## Recommended Next Step

Continue the To-Be adaptation sequence from module completion work:

1. begin the next approved module completion slice, preferably Cockpit
   deep-flow polish or Settings policy-binding UX if the user wants to stay in
   setup/context;
2. create the slice-specific task contract, fixtures, and acceptance tests;
3. validate the module against its Figma deep-flow board and capture browser QA
   evidence;
4. update docs, tests, QA evidence, and GitHub tracking together when the
   product behavior changes.

## 2026-05-27 Cockpit Deep Flow Runtime Slice

Project Cockpit now has the runtime v3 shape:

- backend summary exposes Context Selector, Project Info, Accelerators,
  user-scope, and route-recovery groups;
- `/home` renders Context Selector, Project Info, and Accelerators as primary
  content;
- readiness/metric/recent jobs/recent evidence dashboard panels were removed
  from primary Cockpit content;
- Public View is represented as Context Selector state;
- private context pre-fills project/profile/environment/domain in the selector;
- unknown routes have a visible `Return to Cockpit` path.

Validation:

- `pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q`
  passed with 16 tests.
- `npm test -- src/app/App.test.tsx -t "Cockpit"` passed.
- `npm test -- src/app/AppFunctionalShell.test.tsx` passed.
- Browser QA captured Public View, private scope, accelerator launch/return,
  normal-user restricted visibility, and unknown-route recovery evidence under
  `var/qa/`.

Recommended next step:

Move to the next approved module slice. Given the current To-Be sequence,
Settings policy-binding UX is the best next module completion candidate before
returning to Rates, Assets, Master Data, Integration, and Order Release.

## 2026-05-27 Settings Policy Binding UX Slice

Settings now exposes access-policy binding guidance from the backend:

- `/api/v1/platform/settings/access-model` returns binding scope labels,
  binding requirements, and active-context match state for each access policy;
- scoped setup users still receive only access policies visible to their active
  project;
- the Settings setup surface renders an `Access policy binding review` section
  with project, visibility, domain, and active-context status;
- policy rule JSON remains visible as metadata, while binding rules are
  backend-owned display fields.

Validation:

- `pytest tests/test_operational_context.py -q` passed with 26 tests.
- `npm test -- src/app/App.test.tsx -t "Settings"` passed.
- `npm run build` passed.
- Browser QA captured `var/qa/settings-policy-binding-review.png`.

Recommended next step:

Continue Settings completion by tightening remaining setup flows against the
Configuration Settings deep-flow board: role/grant review, scoped selector
empty/blocked states, and route recovery for setup actions.

## 2026-05-27 Settings Role And Grant Review UX Slice

Settings now exposes grant-binding guidance from the backend:

- `/api/v1/platform/settings/access-model` returns grant scope labels,
  binding requirements, and active-context match state;
- each grant explains user, role, project, environment, and client/domain
  scope;
- the Settings setup surface renders a `Grant binding review` section before
  access-policy authoring;
- scoped setup visibility is preserved by the existing access-model filters.

Validation:

- `pytest tests/test_operational_context.py -q` passed with 26 tests.
- `npm test -- src/app/App.test.tsx -t "Settings"` passed.
- `npm run build` passed.
- Browser QA captured `var/qa/settings-grant-binding-review.png`.

Recommended next step:

Continue Settings completion with setup-action route recovery and blocked/empty
states for scoped selectors, then revalidate against the Configuration Settings
deep-flow board before moving to Rates.

## 2026-05-27 Settings Setup Recovery UX Slice

Settings now handles empty setup states more explicitly:

- the setup authoring panel remains visible even when no workspace/project
  records exist;
- `Setup action recovery` shows backend-owned blocker reasons and action
  disabled reasons;
- setup selectors show compact empty states for missing workspace, project,
  environment, role, and user prerequisites;
- the setup surface includes a visible `Return to Cockpit` link.

Validation:

- `npm test -- src/app/App.test.tsx -t "Settings"` passed with 2 focused tests.
- `npm run build` passed.
- Browser QA captured `var/qa/settings-setup-recovery-empty.png`.

Follow-up:

- Normal non-admin users with no setup authority still hit `Settings is
  unavailable` because audit/feature-flag side queries return `403`. Handle
  this in a scoped-read hardening slice if Settings must be visible to
  read-only/self users.

Recommended next step:

Revalidate Settings against the Configuration Settings deep-flow board and then
move to Rates module completion unless the scoped-read hardening follow-up is
prioritized first.

## 2026-05-27 Settings Final Revalidation

Settings is accepted for the current UI phase with non-blocking follow-ups.

Accepted current-phase scope:

- project/client-domain/environment/profile setup;
- users, roles, grants, and access policies;
- backend-owned blockers/actions;
- grant and policy binding review;
- setup empty-state recovery;
- visible return path to Cockpit.

Out-of-phase Admin Console scope remains deferred:

- separate jobs UI;
- audit search;
- feature flag governance;
- OTM connection governance;
- setup object detail/edit/retire route family.

Validation:

- `npm test -- src/app/App.test.tsx -t "Settings"` passed with 2 focused tests.
- `pytest tests/test_operational_context.py -q` passed with 26 tests.
- `npm run build` passed.

Final Settings review:

- `docs/agent/module-revalidation/SETTINGS_FINAL_REVALIDATION_2026_05_27.md`

Recommended next step:

Start Rates Studio completion against `10 / Rates Studio Deep Flow`.

## 2026-05-27 Rates Route Recovery UX Slice

Rates Studio completion has started with a route-recovery/lifecycle destination
slice:

- `/rates` now renders `Rates lifecycle destinations`;
- module-level recovery links include `Back to Cockpit`, `Back to Rates`,
  `Open batch library`, and `Create rate batch`;
- selected-batch links are generated for batch overview, stage, issues, CSV
  preview, export review, approval review, artifacts, evidence, and Load Plan
  handoff;
- existing backend-owned action execution remains unchanged.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 2 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-route-recovery-lifecycle.png`.

Recommended next step:

Continue Rates completion with a real batch-library/search slice or the
approval/export review route slice. The next highest-value slice is approval
and export review gating, because it addresses the P1 safety finding in the
Rates wireframe brief.

## 2026-05-27 Rates Approval And Export Review UX Slice

Rates approval/export now has explicit review gating:

- approval confirmation renders `Rate approval review` with batch, scenario,
  status, table count, and domain;
- CSV export now opens `Rate export review` with batch, scenario, table count,
  preview count, and client-safe artifact intent;
- `Confirm export` is required before the export endpoint is called;
- the backend-owned `export_csv` action path also opens the review gate instead
  of executing immediately.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 2 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-approval-export-review-gates.png`.

Recommended next step:

Continue Rates completion with a batch-library/search slice, then route-level
batch detail/stage/issues screens.

## 2026-05-27 Rates Batch Library Search UX Slice

Rates now has a real batch-library/search entry point on `/rates`:

- `Rate batch library` consumes the backend-owned batch list endpoint;
- filters include search, status, and domain;
- selecting a filtered row updates the existing selected-batch workspace and
  lifecycle destination links;
- the frontend now treats list items as compact objects because the real
  backend list contract does not include detail-only `tables`.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 2 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-batch-library-search.png`.

Recommended next step:

Continue Rates completion with route-level batch detail/stage/issues screens,
then revalidate the full Rates module against the Figma deep-flow board before
moving to Assets/Load Plan follow-up slices.

## 2026-05-27 Rates Route-Level Batch Screens Slice

Rates now has direct route recovery for the first batch lifecycle screens:

- `/rates/batches/:batchId` renders `Rate batch overview`;
- `/rates/batches/:batchId/stage` renders `Stage rate batch tables` and reuses
  the existing staging action;
- `/rates/batches/:batchId/issues` renders `Rate batch issues` from the
  backend issue-list endpoint;
- each route exposes `Back to Rates` plus adjacent lifecycle navigation.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 3 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-route-level-batch-issues.png` with 4
  backend-generated synthetic validation issues.

Recommended next step:

Continue Rates completion with route-level CSV preview/export/approval screens,
or perform a module-level Rates revalidation if the current route depth is
enough for this cycle.

## 2026-05-27 Rates Route-Level Review Screens Slice

Rates now has direct review routes for the remaining core batch lifecycle:

- `/rates/batches/:batchId/csv-preview` renders `Rate CSV preview`;
- `/rates/batches/:batchId/export` renders `Rate export review`;
- `/rates/batches/:batchId/approve` renders `Rate approval review`;
- export and approval still require explicit confirmation before backend
  execution.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 3 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-route-level-review-screens.png`.

Recommended next step:

Run a final Rates module revalidation against the Figma deep-flow board and
decide whether artifact/evidence/load-plan route screens are needed in this
cycle or can be deferred.

## 2026-05-27 Rates Artifact Evidence Handoff Routes Slice

Rates now closes the remaining batch lifecycle routes:

- `/rates/batches/:batchId/artifacts` renders `Rate batch artifacts` and keeps
  artifact download available from the route-level screen;
- `/rates/batches/:batchId/evidence` renders `Rate batch evidence` with
  backend-owned export/approval evidence;
- `/rates/batches/:batchId/load-plan` renders `Rate Load Plan handoff` with
  batch scope, catalog path, artifact/evidence readiness counts, and a
  `Register Load Plan package` action;
- the handoff action uses the existing
  `/api/v1/modules/load-plan/packages/from-rates/:batchId` endpoint.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 3 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-artifact-evidence-handoff-routes.png`.

Recommended next step:

Run the Rates module revalidation against the Figma deep-flow board, then move
to the next planned module slice once Rates is accepted for this cycle.

## 2026-05-27 Rates Library And New Route Recovery Slice

Rates revalidation against the consolidated deep-flow spec found that
`/rates/batches` and `/rates/batches/new` were visible destinations but not yet
route-specific screens. That gap is now closed:

- `/rates/batches` renders `Rate batch library` with search/status/domain
  filters and a visible `Back to Rates` path;
- `/rates/batches/new` renders `New rate batch` with `Back to batch library`;
- creating a batch from the direct new route navigates to the created batch
  overview;
- the embedded `/rates` create/library behavior remains covered by the same
  functional suite.

Validation:

- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 4 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-library-new-routes.png`.

Recommended next step:

Do one final Rates acceptance checklist pass, then either address the deferred
table detail route or move to the next planned module.

## 2026-05-27 Rates Table Detail Route Slice

The deferred table detail route from the Rates consolidated spec is now in
place:

- backend endpoint:
  `GET /api/v1/modules/rates/batches/{batch_id}/tables/{table_name}`;
- frontend route:
  `/rates/batches/:batchId/tables/:tableName`;
- batch overview table names now open the route-level table detail screen;
- the table screen shows load-order metadata, row count, normalized staged row
  payloads, table-scoped issues, and `Back to Batch`.

Validation:

- `pytest tests/test_rates_batches.py::test_rate_batch_table_detail_returns_rows_and_table_issues -q` passed.
- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 4 tests.
- `npm run build` passed.
- Browser QA captured `var/qa/rates-table-detail-route.png`.

Recommended next step:

Run the final Rates acceptance checklist and then move to the next planned
module slice.

## 2026-05-27 Rates Acceptance Checklist

Rates was revalidated against the consolidated GUI spec and accepted for the
current delivery cycle.

Accepted scope:

- `/rates` hub;
- `/rates/batches` library;
- `/rates/batches/new` create route;
- batch overview;
- stage, issues, table detail, CSV preview, export review, approval review;
- artifacts, evidence, and Load Plan handoff routes.

Fresh validation:

- `pytest tests/test_rates_batches.py -q` passed with 8 tests.
- `pytest tests/test_rates_summary.py -q` passed with 2 tests.
- `pytest tests/test_rates_csv_export_artifacts.py tests/test_rates_batch_approval.py -q` passed with 21 tests.
- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 4 tests.
- `npm run build` passed.

Checklist:

- `docs/agent/RATES_ACCEPTANCE_CHECKLIST_2026-05-27.md`

Backlog retained:

- backend-owned search metadata/operators/pagination;
- row edit/delete and deeper row detail;
- Data Dictionary metadata summary on table detail;
- richer backend eligibility endpoints for export/handoff if needed;
- broader out-of-order browser QA.

Recommended next step:

Start the Assets module slice.

## 2026-05-27 Assets Hub And Library Slice

Assets module completion has started with the first route split:

- `/assets` now renders an Assets Library hub with health metrics, recommended
  route entry points, recent assets, and assets needing attention;
- `/assets/library` preserves the existing backend-backed workflow as the
  temporary functional library route;
- hub entry points are visible for `Open library`, `Create asset`, and
  `Manage classifications`;
- the existing create/version/link/download/archive journey remains covered
  while later slices extract those tasks into dedicated routes.
- Cockpit gained a defensive fallback for older local summary payloads missing
  the newer context/project-info/accelerator groups, which was required to run
  browser QA against the active local backend.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "renders an Assets hub"`
  passed.
- `npm test -- src/app/AppFunctionalAssets.test.tsx` passed with 2 tests.
- `npm test -- src/app/AppFunctionalShell.test.tsx` passed.
- `npm run build` passed.
- `npm run qa:functional:assets:browser` passed.
- Browser QA captured `var/qa/assets-hub-library-route.png`.
- Linear OTM-167 was updated with implementation, validation, evidence, and
  next-step notes.

Task contract:

- `docs/agent/TASK_CONTRACT_ASSETS_HUB_LIBRARY.md`

Recommended next step:

Continue Assets completion with route-level asset detail, then create/edit,
versions, links, classifications, and archive extraction against the Assets
deep-flow board.

## 2026-05-27 Chat Continuity Workflow Guardrail

Status:
Documentation/governance guardrail complete.

Scope:
Analyzed the ways context can be lost between chats and created a durable
new-chat intake plus previous-chat exit workflow.

Files intentionally changed:

- `AGENTS.md`
- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/CHANGE_CONTROL.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/DOCUMENT_INVENTORY.md`

Validation run:

- documentation diff check for the files above;
- no backend/frontend tests were required because this is a documentation-only
  process guardrail.

Validation not run:

- backend tests;
- frontend tests;
- browser QA.

Evidence:

- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`

Open risks:

- The workflow depends on future agents respecting `AGENTS.md` and the handoff
  capsule. This is mitigated by linking the workflow from entry-point docs,
  delivery pipeline, change control, risk register, handoff, and document
  inventory.

Next chat intake notes:

- Start by reading `docs/agent/CHAT_CONTINUITY_WORKFLOW.md` and the newest
  `HANDOFF.md` section before continuing Assets or any other module work.
- Treat the current worktree as dirty and user-owned unless a diff is clearly
  tied to the requested task.

Recommended next step:

Continue the approved module sequence only after running the new-chat intake
gate and confirming the latest user instruction.
