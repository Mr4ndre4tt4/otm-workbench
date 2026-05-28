# Handoff

**Status:** active
**Date:** 2026-05-27

## 2026-05-28 Browser QA Script Classification

Status:
Implemented and validated for GitHub issue #237.

Scope:
Created a governance map for browser QA scripts, marking current-phase scripts
as active, Integration Mapping as reserved, diagnostic scripts as internal,
Assistant as deferred, and Admin/Coordinate Quality top-level scripts as stale
for current acceptance evidence.

Files intentionally changed:

- `docs/agent/BROWSER_QA_SCRIPT_CLASSIFICATION.md`
- `docs/agent/TASK_CONTRACT_BROWSER_QA_SCRIPT_CLASSIFICATION_2026_05_28.md`
- `docs/agent/FRONTEND_CLEANUP_CANDIDATE_CLASSIFICATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `Get-ChildItem frontend/scripts -Filter *.mjs | ForEach-Object { node --check $_.FullName }`
  all scripts parsed successfully.
- `git diff --check`
  passed, with expected Windows CRLF warnings.

Validation not planned:

- Browser screenshots are not planned because the slice classifies evidence
  validity and does not run browser journeys.

Open risks:

- Internal and stale scripts remain callable in `package.json`; removing or
  renaming commands requires a later implementation issue with impact review.

Recommended next step:

Commit, push, open the PR for #237, wait for checks, then merge if green.

## 2026-05-28 Internal GUI Route Guard

Status:
Implemented and validated for GitHub issue #235.

Scope:
Guarded `/__gui/component-gallery` behind the backend-owned navigation contract
when rendered through the app shell, while preserving the standalone component
gallery implementation and component-level test.

Files intentionally changed:

- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/src/app/routes/WorkbenchRoute.test.tsx`
- `frontend/src/app/AppComponentGalleryRoute.test.tsx`
- `docs/agent/TASK_CONTRACT_INTERNAL_GUI_ROUTE_GUARD_2026_05_28.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `npm test -- src/app/routes/WorkbenchRoute.test.tsx src/app/AppComponentGalleryRoute.test.tsx`
  2 files passed, 7 tests passed.
- `git diff --check`
  passed, with expected Windows CRLF warnings.

Validation not planned:

- Browser QA was not planned because this slice only tightens a route guard and
  focused tests; no user-facing module workflow changed.

Open risks:

- Future use of the component gallery through the app shell should add an
  explicit backend navigation/capability contract first.

Recommended next step:

Commit, push, open the PR for #235, wait for checks, then merge if green.

## 2026-05-28 Rates Same-Name Context Isolation

Status:
Implemented and validated for GitHub issue #216.

Scope:
Added focused backend regression coverage proving same-name Rates batches do
not leak across active domain or environment scope, while DBA/all-domain
visibility remains constrained to the active environment.

Files intentionally changed:

- `tests/test_rates_batches.py`
- `docs/agent/TASK_CONTRACT_RATES_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `python -m pytest tests/test_rates_batches.py -k "same_name or active_context_scope or dba_context" -q`:
  5 passed, 5 deselected.
- `python -m pytest tests/test_rates_batches.py tests/test_rates_summary.py -q`:
  12 passed.

Validation not run:

- Browser QA was not run because this slice only adds backend context-isolation
  regression coverage and does not change visible UI behavior.

Evidence:

- GitHub issue #216 tracks the delivery slice.
- New tests assert visible and hidden batch IDs plus direct detail route access
  for same-name batches.

Open risks:

- The local workspace remains dirty with unrelated parallel work; future
  commits must keep staging scoped.

Next-chat intake notes:

- Integration Mapping remains reserved for its dedicated chat.
- Treat unrelated dirty frontend, Assistant, Assets, Load Plan, and
  `OTM_RESOURCES/` changes as out of scope for this Rates slice unless the
  latest user instruction says otherwise.

Recommended next step:

Push the scoped #216 commit, wait for GitHub checks, close the issue, then pick
the next small context-isolation follow-up from the validation matrix.

## 2026-05-28 Master Data Same-Name Context Isolation

Status:
Implemented and validated for GitHub issue #217.

Scope:
Added focused backend regression coverage proving same-name Master Data
workbook batches do not leak across active project, domain, or environment
scope, while DBA/all-domain visibility remains constrained to the active
environment.

Files intentionally changed:

- `tests/test_master_data_templates.py`
- `docs/agent/TASK_CONTRACT_MASTER_DATA_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `python -m pytest tests/test_master_data_templates.py -k "same_name or active_context_scope or dba_context" -q`:
  4 passed, 56 deselected.
- `python -m pytest tests/test_master_data_templates.py -k "context_scope or dba_context or same_name or require_active_context" -q`:
  5 passed, 55 deselected.

Validation not run:

- Browser QA was not run because this slice only adds backend
  context-isolation regression coverage and does not change visible UI
  behavior.

Evidence:

- GitHub issue #217 tracks the delivery slice.
- New tests assert visible and hidden batch IDs plus direct detail/output/csv
  route access for same-name workbook batches.

Open risks:

- The local workspace remains dirty with unrelated parallel work; future
  commits must keep staging scoped.

Next-chat intake notes:

- Integration Mapping remains reserved for its dedicated chat.
- Treat unrelated dirty frontend, Assistant, Assets, Load Plan, and
  `OTM_RESOURCES/` changes as out of scope for this Master Data slice unless
  the latest user instruction says otherwise.

Recommended next step:

Push the scoped #217 commit, wait for GitHub checks, close the issue, then
pick the next small context-isolation follow-up from the validation matrix.

## 2026-05-28 Order Release Same-Name Context Isolation

Status:
Implemented and validated for GitHub issue #218.

Scope:
Added focused backend regression coverage proving same-name Order Release
templates and batches do not leak across active project, domain, or environment
scope, while DBA/all-domain visibility remains constrained to the active
environment.

Files intentionally changed:

- `tests/test_order_release_generator_foundation.py`
- `tests/test_order_release_generator_batches.py`
- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_SAME_NAME_CONTEXT_ISOLATION.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -k "same_name or active_context_scope or dba_context" -q`:
  8 passed, 19 deselected.
- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -q`:
  27 passed.

Validation not run:

- Browser QA was not run because this slice only adds backend
  context-isolation regression coverage and does not change visible UI
  behavior.

Evidence:

- GitHub issue #218 tracks the delivery slice.
- New tests assert visible and hidden IDs plus direct template versioning,
  batch creation, detail, and preview route access for same-name records.

Open risks:

- Template `code` remains a global version-family identity; same-code
  cross-scope template authoring is not supported by the current backend
  validator even though same-name templates are scoped.
- The local workspace remains dirty with unrelated parallel work; future
  commits must keep staging scoped.

Next-chat intake notes:

- Integration Mapping remains reserved for its dedicated chat.
- Treat unrelated dirty frontend, Assistant, Assets, Load Plan, and
  `OTM_RESOURCES/` changes as out of scope for this Order Release slice unless
  the latest user instruction says otherwise.

Recommended next step:

Push the scoped #218 commit, wait for GitHub checks, close the issue, then
continue with Cockpit browser route recovery/visual evidence if the user asks
for the next context-isolation item.

## 2026-05-28 Context Isolation Matrix Sync

Status:
Implemented and validated for GitHub issue #219.

Scope:
Synchronized the context isolation matrix so completed Cockpit, Rates, Master
Data, and Order Release validation slices are recorded as completed evidence
instead of future gaps.

Files intentionally changed:

- `docs/agent/CONTEXT_ISOLATION_VALIDATION_MATRIX.md`
- `docs/agent/TASK_CONTRACT_CONTEXT_ISOLATION_MATRIX_SYNC_2026_05_28.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

Validation run:

- `python -m pytest tests/test_operational_context.py -q`: 26 passed.
- `python -m pytest tests/test_modules_navigation.py -q`: 10 passed.

Validation not run:

- Browser QA was not run because this slice only synchronizes governance
  documentation and does not change visible UI behavior.

Evidence:

- GitHub issue #219 tracks the documentation sync.

Open risks:

- The local workspace remains dirty with unrelated parallel work; future
  commits must keep staging scoped.

Next-chat intake notes:

- Integration Mapping remains reserved for its dedicated chat.
- Treat unrelated dirty frontend, Assistant, Assets, Load Plan, and
  `OTM_RESOURCES/` changes as out of scope for this governance sync unless the
  latest user instruction says otherwise.

Recommended next step:

Push the scoped #219 commit, wait for GitHub checks, close the issue, then
continue with the next roadmap item from the refreshed matrix.

## 2026-05-28 Assets Acceptance Pass

Status:
Accepted for current delivery cycle.

Scope:
Completed GitHub issue #197 by comparing Assets Library against the consolidated
Assets spec, recording the current-cycle acceptance decision, and creating
GitHub backlog issues for accepted deferrals.

What changed:

- created `docs/agent/ASSETS_ACCEPTANCE_CHECKLIST_2026-05-28.md`;
- created `docs/agent/TASK_CONTRACT_ASSETS_ACCEPTANCE_PASS.md`;
- updated `docs/agent/DOCUMENT_INVENTORY.md` with the acceptance checklist;
- updated #195 with completed #196, in-progress #197, and backlog links;
- commented #197 with backlog closeout status;
- created backlog issues #198, #199, and #200.

Acceptance decision:

Assets Library is accepted for the current delivery cycle. The module now covers
hub, library search, create, detail, edit metadata, versions, upload, links,
classification management, guarded download, and archive with backend-owned
validation and route-level recovery.

Backlog retained:

- #198 route-optimized detail and archive impact contracts;
- #199 batch/checklist link target lookup;
- #200 target OTM version taxonomy validation;
- restore/deprecate lifecycle variants and create-with-file shortcut remain
  future enhancements.

Validation run:

- Assets spec and implementation evidence review;
- GitHub issue create/edit/comment for #195 and #197-#200;
- `git diff --cached --check` before commit.

Validation reused from #196:

- Assets backend suite: 50 passed;
- Assets functional suite: 13 passed;
- frontend build passed with existing Vite large chunk warning;
- browser QA passed after runtime freshness gate.

Validation not run:

- full repository backend suite;
- full repository frontend suite;
- new browser QA, because this slice only records acceptance based on the latest
  #196 Assets validation evidence.

Open risks:

- future Assets enhancements must use the backlog issues instead of expanding
  accepted current-cycle scope silently.
- unrelated Assistant and Integration Mapping work remains outside this slice.

Recommended next step:
Close #197 and #195 after push, then move to the next approved module slice.
Recommended default: Master Data / Data Factory foundation unless the user
prioritizes another non-Integration-Mapping module.
## 2026-05-28 Assets Target OTM Version Search

Status:
Implemented and validated.

Scope:
Completed GitHub issue #196 for `v0.3-assets-stabilization` by adding
backend-owned `target_otm_version` metadata and exposing it in the Assets
Library UI.

What changed:

- added `assets.target_otm_version` with Alembic migration;
- create/update/serialize now carry normalized target OTM version metadata;
- `GET /api/v1/modules/assets/assets` supports `target_otm_version` and
  `target_otm_version_operator`;
- Assets forms expose `Asset target OTM version`;
- `/assets/library` exposes target OTM version filter/operator controls;
- browser QA exercises the target OTM version filter and reset behavior.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ASSETS_TARGET_OTM_VERSION_SEARCH.md`
- `migrations/versions/c1f4a8e7d9b2_assets_target_otm_version.py`
- `src/otm_workbench/models.py`
- `src/otm_workbench/modules/assets/assets.py`
- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `frontend/src/platform/types/assets.ts`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "target_otm_version or table_exists" -q`:
  failed first, then passed with 2 tests.
- `python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py -q`:
  50 passed.
- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"`:
  failed first, then passed with 1 passed and 12 skipped.
- `npm test -- src/app/AppFunctionalAssets.test.tsx`: 13 passed.
- `npm run build`: passed with the existing Vite large chunk warning.
- `python -m alembic heads`: `c1f4a8e7d9b2 (head)`.
- `npm run qa:functional:assets:browser`: passed.

Browser QA:

- backend: `http://127.0.0.1:8025`;
- frontend: `http://127.0.0.1:5204`;
- database: `var/qa-assets-target-otm-version.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- backend/frontend QA runtimes have no listeners after validation.

Open risks:

- this slice normalizes target OTM version as a safe token and does not yet
  validate it against an official Oracle release taxonomy.
- unrelated Assistant and Integration Mapping work remains outside this slice.

Recommended next step:
Close #196 after push and continue with #197, the Assets acceptance pass and
backlog closeout.
## 2026-05-28 Assets Version Train Setup

Status:
GitHub version train created.

Scope:
Created the next small-commit delivery lane for Assets stabilization so future
work starts from GitHub issues instead of accumulating silently in the local
workspace.

GitHub changes:

- assigned governance issue #194 to milestone `Governance Reset`;
- created version issue #195: `[Version]: v0.3-assets-stabilization`;
- assigned #195 to milestone `Assets`;
- created child issue #196: `[Slice]: Assets target OTM version search contract`;
- created child issue #197: `[Slice]: Assets acceptance pass and backlog closeout`;
- updated #195 with child links;
- commented #194 and PR #182 with the operational follow-up.

Validation run:

- `C:\Program Files\GitHub CLI\gh.exe issue list --repo Mr4ndre4tt4/otm-workbench --state open --limit 60 --json number,title,labels,milestone,updatedAt,url`;
- `C:\Program Files\GitHub CLI\gh.exe api repos/Mr4ndre4tt4/otm-workbench/milestones --paginate`;
- GitHub issue create/edit/comment commands for #194-#197.

Validation not run:

- backend tests;
- frontend tests;
- browser QA.

Reason:
This slice only changed GitHub delivery tracking and handoff documentation.

Recommended next step:
Start #196 if we want one more Assets implementation slice, or start #197 if we
want to close Assets with an acceptance/backlog pass before moving modules.
## 2026-05-28 GitHub Versioning And Issue Cadence

Status:
Governance rule documented; GitHub tracking issue created.

Scope:
Adopt lightweight GitHub version trains, smaller issue-linked commits, and more
frequent issue updates so large local workspace batches do not become hidden
project state.

What changed:

- created GitHub issue #194 for the governance slice;
- documented version-tracking via milestone when available or version issue as
  fallback;
- added issue cadence rules for task contracts, implementation starts,
  validation results, and deferred follow-ups;
- added commit granularity guidance for backend, frontend, governance,
  validation, and artifact slices;
- updated the delivery pipeline, change control, roadmap, risk register,
  decision log, document inventory, AGENTS, and GitHub governance docs.

Files intentionally changed:

- `AGENTS.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/CHANGE_CONTROL.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `docs/otm-workbench/governance/GITHUB_DELIVERY_GOVERNANCE.md`
- `docs/otm-workbench/governance/GITHUB_VERSIONING_AND_ISSUE_CADENCE.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- GitHub issue #194 created through the GitHub connector;
- documentation diff review;
- `git diff --cached --check` before commit.

Validation not run:

- backend tests;
- frontend tests;
- browser QA.

Reason:
This slice is documentation and governance only. It does not change runtime
behavior.

Open risks:

- GitHub CLI is installed at `C:\Program Files\GitHub CLI\gh.exe`, version
  2.92.0, and authenticated as `Mr4ndre4tt4`; this shell may require the
  absolute path when `gh` is not on PATH.
- Parallel local Assistant and Integration Mapping work remains outside this
  governance commit.

Recommended next step:
Use issue #194 as the tracking point until the first version train is named,
then create or update issues at the start of each meaningful slice.
## 2026-05-28 Assets Linked Target Search UI

Status:
Implemented and validated.

Scope:
The `/assets/library` frontend now exposes the backend-owned linked target type
filter that was added to the Assets list API.

What changed:

- added `Asset linked target type filter` sourced from asset link
  classifications;
- added `Asset linked target type operator` with `one_of` and `not_one_of`;
- applying search sends `linked_target_type` and
  `linked_target_type_operator`;
- reset search clears linked target type and restores `one_of`;
- browser QA now exercises the linked target type filter;
- Storybook was treated as optional support and not used for this small
  in-context form extension.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ASSETS_LINKED_TARGET_SEARCH_UI.md`
- `docs/superpowers/plans/2026-05-28-assets-linked-target-search-ui.md`
- `frontend/src/platform/types/assets.ts`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"`:
  1 passed, 12 skipped after expected red failure was fixed.
- `npm test -- src/app/AppFunctionalAssets.test.tsx`: 13 passed.
- `npm run build`: passed with existing Vite large chunk warning.
- `npm run qa:functional:assets:browser`: passed.

Browser QA:

- backend: `http://127.0.0.1:8024`;
- frontend: `http://127.0.0.1:5203`;
- database: `var/qa-assets-linked-target-ui.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- backend/frontend QA runtimes were stopped after validation.

Open risks:

- target OTM version search remains deferred.
- `OTM_RESOURCES/`, `outputs/`, Integration Mapping, and assistant-planning
  changes remain outside this slice.
- Integration Mapping remains reserved for its dedicated chat/workstream unless
  explicitly requested.

Recommended next step:
Commit and push this UI slice, then evaluate whether target OTM version needs a
real model/API contract or should remain deferred.
## 2026-05-28 Assets Linked Target Search API

Status:
Implemented and backend validated.

Scope:
The Assets Library list endpoint now supports backend-owned filtering by linked
target type using existing `AssetLink.link_type` records.

What changed:

- `GET /api/v1/modules/assets/assets` accepts `linked_target_type`;
- `linked_target_type_operator=one_of` accepts comma-separated link types;
- `linked_target_type_operator=not_one_of` excludes assets linked to the given
  type while retaining unlinked assets;
- unsupported linked target operators return `ASSET_SEARCH_INVALID_OPERATOR`;
- no new database columns or frontend controls were added in this slice.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ASSETS_LINKED_TARGET_SEARCH_API.md`
- `docs/superpowers/plans/2026-05-28-assets-linked-target-search-api.md`
- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "linked_target_type"`:
  2 passed, 21 deselected after the expected red failure was fixed.
- `python -m pytest tests/test_assets_library_assets.py`: 23 passed.
- `python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py`:
  49 passed.

Open risks:

- frontend linked target type filter UI remains deferred.
- target OTM version search remains deferred.
- `OTM_RESOURCES/`, `outputs/`, and unrelated assistant-planning files remain
  untracked and outside this slice.
- Integration Mapping remains reserved for its dedicated chat/workstream unless
  explicitly requested.

Recommended next step:
Commit and push this backend/API slice, then add the frontend linked target type
filter control or move to another non-Integration-Mapping roadmap item.
## 2026-05-28 Assets Library Row Actions

Status:
Implemented and validated.

Scope:
The `/assets/library` search results now expose explicit route-level row
actions while preserving the in-page selected-asset workflow.

What changed:

- library result rows now render with action-capable `DetailList` rows;
- each row exposes `Open <asset>` to `/assets/:assetId`;
- eligible rows expose `Upload version for <asset>` to
  `/assets/:assetId/versions/new`;
- eligible rows expose `Archive <asset>` to `/assets/:assetId/archive`;
- each row also keeps a `Select <asset>` button so the existing workflow panels
  can still load the row without leaving `/assets/library`;
- functional coverage now asserts row action links.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ASSETS_LIBRARY_ROW_ACTIONS.md`
- `docs/superpowers/plans/2026-05-28-assets-library-row-actions.md`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "library row actions"`:
  1 passed, 12 skipped after the expected red failure was fixed.
- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"`:
  1 passed, 12 skipped.
- `npm test -- src/app/AppFunctionalAssets.test.tsx`: 13 passed.
- `npm run build`: passed with the existing Vite large chunk warning.
- `npm run qa:functional:assets:browser`: passed.

Browser QA:

- backend: `http://127.0.0.1:8023`;
- frontend: `http://127.0.0.1:5202`;
- database: `var/qa-assets-row-actions.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- backend/frontend QA runtimes were stopped after validation.

Open risks:

- linked target type and target OTM version search remain deferred.
- `OTM_RESOURCES/`, `outputs/`, and unrelated assistant-planning files remain
  untracked and outside this slice.
- Integration Mapping remains reserved for its dedicated chat/workstream unless
  explicitly requested.

Recommended next step:
Commit and push this row-actions slice, then continue with another
non-Integration-Mapping Assets acceptance item or move to the next roadmap
module the user requests.
## 2026-05-28 Assets Library Search UI

Status:
Implemented and validated.

Scope:
The `/assets/library` frontend now consumes the backend-owned
search/operator/pagination contract for Assets Library.

What changed:

- added `Asset name search` and `Asset description search`;
- added operator controls for name, description, module id, macro object, and
  OTM table;
- kept existing type, category, status, tag, scope, module, macro object, and
  OTM table filters;
- renamed the library actions to `Apply search` and `Reset search`;
- added `Asset page size`, visible result count, and previous/next page
  controls;
- updated the Assets functional test to assert query params for text operators
  and page size;
- updated browser QA to exercise the new search controls and capture
  `var/qa/assets-library-search.png`.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ASSETS_LIBRARY_SEARCH_UI.md`
- `docs/superpowers/plans/2026-05-28-assets-library-search-ui.md`
- `frontend/src/platform/types/assets.ts`
- `frontend/src/platform/hooks/assets.ts`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"`:
  1 passed, 11 skipped after the expected red failure was fixed.
- `npm test -- src/app/AppFunctionalAssets.test.tsx`: 12 passed.
- `npm run build`: passed with the existing Vite large chunk warning.
- `npm run qa:functional:assets:browser`: passed.

Browser QA:

- backend: `http://127.0.0.1:8022`;
- frontend: `http://127.0.0.1:5201`;
- database: `var/qa-assets-search-ui.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- new screenshot: `var/qa/assets-library-search.png`;
- backend/frontend QA runtimes were stopped after validation.

Open risks:

- linked target type and target OTM version search are still deferred.
- `OTM_RESOURCES/`, `outputs/`, and unrelated assistant-planning files remain
  untracked and outside this slice.
- Integration Mapping remains reserved for its dedicated chat/workstream unless
  explicitly requested.

Recommended next step:
Commit and push this UI slice, then continue with another non-Integration
Mapping Assets acceptance item or move to the next roadmap module the user
requests.

## 2026-05-27 Integration Mapping Guard And Assets Search API

Status:
Implemented and backend validated.

Scope:
The user reserved Integration Mapping for a separate dedicated Solon-governed
chat/workstream. This chat should avoid Integration Mapping changes unless the
user explicitly asks, the chat is already in Integration Mapping context, or a
minimal cross-module adjustment is required by another module.

The Assets Library backend list endpoint now has a first backend-owned
search/operator/pagination contract.

What changed:

- `GET /api/v1/modules/assets/assets` now supports `page` and `page_size`;
- the response preserves full filtered `total` plus returned `page` and
  `page_size`;
- text/operator filters are available for asset id, name, description, module
  id, macro object, and OTM table;
- supported operators are `begins_with`, `contains`, `one_of`, and
  `not_one_of`;
- existing exact filters remain compatible for asset type, category, status,
  visibility, sensitivity, scope, tag, module, macro object, and OTM table;
- invalid operators return `ASSET_SEARCH_INVALID_OPERATOR`;
- the stale permissions test was aligned with the current active-context rule:
  non-admin users without active context cannot read operational assets.

Files intentionally changed:

- `AGENTS.md`
- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/TASK_CONTRACT_ASSETS_LIBRARY_SEARCH_API.md`
- `docs/superpowers/plans/2026-05-27-assets-library-search-api.md`
- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `tests/test_assets_library_permissions.py`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "backend_search_operators or pagination_metadata or invalid_search_operator"`
  failed before implementation as expected.
- The same focused command passed after implementation: 3 passed, 18
  deselected.
- `python -m pytest tests/test_assets_library_assets.py` -> 21 passed.
- `python -m pytest tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py`
  -> 9 passed.
- `python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py`
  -> 47 passed.

Validation not run:

- `python -m pytest tests/test_assets_library_*.py` was attempted, but
  PowerShell did not expand the glob and pytest collected 0 tests. The explicit
  file-list command above replaced it.
- Browser QA was not run because this slice is backend/API-only.

Evidence:

- No screenshot evidence captured for this backend/API slice.

Open risks:

- The frontend search-builder UI still needs to consume this backend contract.
- `OTM_RESOURCES/` and `outputs/` remain untracked/protected and unrelated.
- Integration Mapping should be treated as reserved parallel work.

Next-chat intake notes:

- Start by reading this handoff, then inspect `git status --short` and diffs
  before editing.
- Do not touch Integration Mapping unless the latest user request permits it.
- If continuing Assets, the next useful slice is the `/assets/library`
  frontend search-builder UI that consumes the new backend operators.

Recommended next step:
Commit and push this backend/API slice, then start the Assets frontend
search-builder UI or switch to another non-Integration-Mapping roadmap item
requested by the user.

## 2026-05-27 Assets Detail Actions Cleanup

Status:
Implemented and fully validated.

Scope:
The `/assets/:assetId` detail route now exposes the action set documented in
the consolidated Assets spec.

What changed:

- detail action labels now include `Upload version`, `View versions`, and
  `Manage links`;
- detail route adds a guarded `Download current version` button;
- detail route adds `Archive asset` navigation to
  `/assets/:assetId/archive`;
- success/error feedback now renders on the detail route for direct downloads;
- browser QA checks the direct detail actions and captures
  `var/qa/assets-detail-actions-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"` ->
  1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 12 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `node scripts/functional-assets-browser.mjs` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8021`;
- frontend: `http://127.0.0.1:5199`;
- database: `var/qa-assets-detail-actions.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots include `var/qa/assets-detail-actions-route.png`,
  `var/qa/assets-create-route.png`, `var/qa/assets-classifications-route.png`,
  `var/qa/assets-classification-create-route.png`,
  `var/qa/assets-classification-edit-route.png`,
  `var/qa/assets-archive-route.png`, `var/qa/assets-links-route.png`,
  `var/qa/assets-version-upload-route.png`, `var/qa/assets-versions-route.png`,
  `var/qa/assets-edit-metadata-route.png`, `var/qa/assets-detail-route.png`.

Next-chat intake notes:

- `OTM_RESOURCES/` and `outputs/` remain untracked and unrelated.
- Browser QA runtime `8021/5199` was stopped after validation.

Recommended next step:
Start planning the `/assets/library` backend-owned search/operator/pagination
slice, since the remaining Assets acceptance gaps are now backend/API-sized.

## 2026-05-27 Assets Acceptance Create Route Cleanup

Status:
Implemented and fully validated.

Scope:
Assets Library now has a dedicated `/assets/new` route-level create screen, and
asset creation no longer contains classification authoring.

What changed:

- `/assets/new` renders `Create asset` with `Back to Library`, `Cancel`, and
  `Manage classifications`;
- `/assets/new` uses the existing backend asset create contract;
- the create route disables selected-asset hydration so it starts from the
  default synthetic draft instead of copying the first/selected asset;
- the legacy create workflow no longer renders `Asset classification
  authoring`;
- the long Assets functional journey and browser QA now create classifications
  only through `/assets/classifications/*`;
- browser QA captures `var/qa/assets-create-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "dedicated route without
  classification authoring"` -> 1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 12 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `node scripts/functional-assets-browser.mjs` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8020`;
- frontend: `http://127.0.0.1:5198`;
- database: `var/qa-assets-create-route.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots include `var/qa/assets-create-route.png`,
  `var/qa/assets-classifications-route.png`,
  `var/qa/assets-classification-create-route.png`,
  `var/qa/assets-classification-edit-route.png`,
  `var/qa/assets-archive-route.png`, `var/qa/assets-links-route.png`,
  `var/qa/assets-version-upload-route.png`, `var/qa/assets-versions-route.png`,
  `var/qa/assets-edit-metadata-route.png`, `var/qa/assets-detail-route.png`.

Next-chat intake notes:

- `OTM_RESOURCES/` and `outputs/` remain untracked and unrelated.
- Browser QA runtime `8020/5198` was stopped after validation.
- The remaining Assets acceptance gaps are backend/API-sized work, not this
  small create-route cleanup.

Recommended next step:
Plan the `/assets/library` backend-owned search/operator/pagination slice, or
do a small detail-route actions cleanup if we want to keep the next change
frontend-only.

## 2026-05-27 Assets Classifications Routes Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has route-level classification list, create, and edit
screens at `/assets/classifications`, `/assets/classifications/new`, and
`/assets/classifications/:classificationId/edit`.

What changed:

- `/assets/classifications` renders backend-owned classification groups and
  separates classification management from the asset workflow rail;
- `/assets/classifications/new` creates a classification through the existing
  backend `POST /api/v1/modules/assets/classifications` contract;
- `/assets/classifications/:classificationId/edit` patches editable
  classification fields through the existing backend PATCH contract;
- system-protected rows render as guarded system rows instead of edit actions;
- the shared `module-form-grid` CSS now gives route-level forms stable,
  responsive field layout;
- browser QA now captures classification list, create, and edit evidence before
  running the existing Assets lifecycle journey.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset classification"`
  -> 3 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 11 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `node scripts/functional-assets-browser.mjs` -> passed.

Browser QA:

- backend: `http://127.0.0.1:8019`;
- frontend: `http://127.0.0.1:5197`;
- database: `var/qa-assets-classifications-routes.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots: `var/qa/assets-classifications-route.png`,
  `var/qa/assets-classification-create-route.png`,
  `var/qa/assets-classification-edit-route.png`,
  `var/qa/assets-archive-route.png`, `var/qa/assets-links-route.png`,
  `var/qa/assets-version-upload-route.png`, `var/qa/assets-versions-route.png`,
  `var/qa/assets-edit-metadata-route.png`, `var/qa/assets-detail-route.png`.

Next-chat intake notes:

- The valid browser QA frontend is `5197` with `VITE_DEV_PROXY_TARGET`; the
  earlier `5196` attempt used `VITE_API_BASE_URL` and failed CORS preflight.
- `OTM_RESOURCES/` remains intentionally untracked and must stay out of this
  commit.
- `outputs/` is also untracked and unrelated to this slice.

Recommended next step:
Run an Assets acceptance pass against the consolidated Assets spec, then decide
whether to remove or keep the legacy classification authoring bridge inside the
asset creation workflow.

## 2026-05-27 Assets Archive Route Slice

Status:
Implemented and fully validated.

Scope:
Assets Library now has a route-level archive review screen at
`/assets/:assetId/archive`.

What changed:

- `/assets/:assetId/archive` renders archive impact and confirmation for one
  asset;
- the screen shows lifecycle status, current version file/id, version count,
  linked target count, visibility, and sensitivity;
- `Archive asset` uses the existing backend archive endpoint and disables after
  the asset reaches `ARCHIVED`;
- the archive route exposes `Back to Asset`, `Back to Library`, and `Cancel`;
- browser QA now archives through the direct route and captures
  `var/qa/assets-archive-route.png`.

Validation:

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "archives an asset"` ->
  1 passed;
- `npm test -- src/app/AppFunctionalAssets.test.tsx` -> 8 passed;
- `npm run build` -> passed with the existing Vite large chunk warning;
- `npm run qa:functional:assets:browser` -> passed;
- `git diff --check` -> no errors, LF/CRLF warnings only.

Browser QA:

- backend: `http://127.0.0.1:8018`;
- frontend: `http://127.0.0.1:5195`;
- database: `var/qa-assets-archive-route.db`;
- live navigation IDs: `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`;
- screenshots: `var/qa/assets-archive-route.png`,
  `var/qa/assets-links-route.png`, `var/qa/assets-version-upload-route.png`,
  `var/qa/assets-versions-route.png`, `var/qa/assets-edit-metadata-route.png`,
  `var/qa/assets-detail-route.png`.

Recommended next step:
Continue Assets route extraction with classification list/create/edit route
refinement, then run an Assets acceptance pass against the consolidated spec.

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

## 2026-05-28 Context Segregation Foundation GitHub Closure

Status:
GitHub tracking closure complete.

Scope:
Revalidated the already documented context segregation foundation and closed
GitHub issue #184. No application code changed in this closure slice.

Validation run:

- `python -m pytest tests/test_operational_scope.py -q` passed with 6 tests.
- `python -m pytest tests/test_modules_navigation.py -q` passed with 10 tests.
- `python -m pytest tests/test_operational_context.py -vv -s` passed with 26
  tests.
- `python -m pytest tests/test_operational_metadata.py -q` passed with 23
  tests.

Validation note:

- The first broad combined pytest command timed out on Windows without useful
  output. The same representative scope packages passed when split.

GitHub:

- Closed #184: `[Slice]: implement context segregation foundation`.
- Added issue comment with the validation evidence and closure rationale.

Recommended next step:

Continue with #185 Settings policy/access setup or #186 Cockpit context and
accelerator launch, keeping Integration Mapping reserved for its separate
workstream unless explicitly requested.

## 2026-05-28 Settings Functional QA Sync

Status:
Implemented and validated.

Scope:
Continued GitHub issue #185 by updating the stale functional Admin frontend QA
test to validate the current Settings route and setup/access-policy surface
instead of the older Admin Console / Jobs acceptance path.

Files intentionally changed:

- `frontend/src/app/AppFunctionalAdmin.test.tsx`
- `docs/agent/TASK_CONTRACT_SETTINGS_FUNCTIONAL_QA_SYNC.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm run qa:functional:admin` passed with 1 test.
- `npm test -- src/app/App.test.tsx -t "Settings"` passed with 2 tests.
- `python -m pytest tests/test_operational_context.py -q` passed with 26
  tests.
- `npm run build` passed with the existing Vite large chunk warning.
- `git diff --check -- frontend/src/app/AppFunctionalAdmin.test.tsx` passed.

Validation not run:

- Fresh browser QA. Existing Settings browser evidence remains the accepted
  visual evidence for #185; the legacy browser script still expects old Admin
  Console/Jobs language and should be updated before it is reused as fresh
  evidence.

Recommended next step:

Close #185 after push, then continue with #186 Cockpit context and accelerator
launch flow.

## 2026-05-28 Cockpit GitHub Closure

Status:
Accepted for current UI phase and GitHub closure ready.

Scope:
Revalidated GitHub issue #186 against the current Cockpit v3 target: Context
Selector, Project Info, Public View state, and accelerator launcher without
readiness/workstream/blocker/job/activity dashboard behavior.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_COCKPIT_GITHUB_CLOSURE.md`
- `docs/agent/module-revalidation/COCKPIT_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q` passed with 17 tests.
- `npm test -- src/app/App.test.tsx -t "Cockpit"` passed with 1 test.
- `npm test -- src/app/AppFunctionalShell.test.tsx -t "persists backend-owned context"` passed with 1 test.

Evidence reused:

- `var/qa/cockpit-public-view.png`
- `var/qa/cockpit-private-scope-viewport.png`
- `var/qa/cockpit-scoped-user.png`
- `var/qa/cockpit-route-recovery.png`

Validation not run:

- Fresh browser screenshots. The prior Cockpit v3 browser evidence remains the
  accepted visual evidence; this slice only performs automated revalidation and
  GitHub/docs closure.

Open risks:

- The older consolidated Cockpit spec still includes command-center dashboard
  language and should be rewritten or marked superseded in a later docs cleanup.
- Parallel shell/assistant and Integration Mapping work remains outside this
  closure.

Recommended next step:

Close #186 after push, then continue with #187 Rates Studio revalidation.

## 2026-05-28 Rates Final Revalidation

Status:
Accepted for current UI phase and GitHub closure ready.

Scope:
Revalidated GitHub issue #187 against the active Rates Studio To-Be batch
lifecycle: hub, batch library, creation, overview/detail, staging, table
detail, issues, CSV preview, export review, approval review, artifacts,
evidence, and Load Plan handoff.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_RATES_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/RATES_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_rates_batches.py -q` passed with 8 tests.
- `python -m pytest tests/test_rates_summary.py -q` passed with 2 tests.
- `python -m pytest tests/test_rates_csv_export_artifacts.py tests/test_rates_batch_approval.py -q` passed with 21 tests.
- `python -m pytest tests/test_rates_dictionary.py tests/test_rates_csv_preview.py -q` passed with 14 tests.
- `python -m pytest tests/test_rates_batch_validation.py tests/test_rates_batch_scenarios.py tests/test_rates_batch_csv_preview.py -q` passed with 20 tests.
- `npm test -- src/app/AppFunctionalRates.test.tsx` passed with 4 tests.
- `npm run build` passed with the existing Vite large chunk warning.

Evidence reused:

- `var/qa/rates-batch-library-search.png`
- `var/qa/rates-library-new-routes.png`
- `var/qa/rates-table-detail-route.png`
- `var/qa/rates-route-level-batch-issues.png`
- `var/qa/rates-route-level-review-screens.png`
- `var/qa/rates-approval-export-review-gates.png`
- `var/qa/rates-artifact-evidence-handoff-routes.png`
- `var/qa/rates-route-recovery-lifecycle.png`

Validation not run:

- Fresh browser screenshots. Existing Rates route-level browser evidence remains
  accepted visual evidence for #187; any future screenshot capture must first
  pass the `/api/v1/platform/navigation` runtime freshness gate.

Open risks:

- Backend-owned advanced search metadata/operators, pagination, row mutation,
  Data Dictionary metadata summary, and expanded blocked-path browser QA remain
  backlog, not blockers for the current To-Be sequence.
- Parallel shell/assistant and Integration Mapping work remains outside this
  closure.

Recommended next step:

Close #187 after push, then choose the next tracked roadmap issue outside
Rates unless the user explicitly asks for one of the backlog items.

## 2026-05-28 Master Data Final Revalidation

Status:
Accepted for current UI phase and GitHub closure ready.

Scope:
Revalidated GitHub issue #203 against the active Master Data / Data Factory
To-Be route-family model: Data Factory, Template Builder, and Quality Tools as
separate operational, authoring, and quality workflows.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_MASTER_DATA_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/MASTER_DATA_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_master_data_direct_otm_import_guard.py -q`
  passed with 5 tests.
- `python -m pytest tests/test_coordinate_quality_api.py tests/test_coordinate_quality_engine.py -q`
  passed with 15 tests.
- `python -m pytest tests/test_master_data_templates.py -q` passed with 58
  tests.
- `npm test -- src/app/AppFunctionalMasterData.test.tsx src/app/AppFunctionalCoordinateQuality.test.tsx`
  passed with 7 tests.
- `npm test -- src/app/App.test.tsx -t "Master Data"` passed with 4 tests and
  26 skipped tests.
- `npm run build` passed with the existing Vite large chunk warning.

Evidence reused:

- `output/gui-qa/master-data/01-master-data-hub.png`
- `output/gui-qa/master-data/02-template-builder-entry.png`
- `output/gui-qa/master-data/02-template-builder-search.png`
- `output/gui-qa/master-data/02-template-builder-detail.png`
- `output/gui-qa/master-data/02-template-builder-copy.png`
- `output/gui-qa/master-data/02-template-builder-copy-created.png`
- `output/gui-qa/master-data/02-template-builder-edit.png`
- `output/gui-qa/master-data/02-template-builder-retire.png`
- `output/gui-qa/master-data/02-template-builder-new.png`
- `output/gui-qa/master-data/03-data-factory-entry.png`
- `output/gui-qa/master-data/04-template-detail-regions-basic.png`
- `output/gui-qa/master-data/05-batch-detail-input.png`
- `output/gui-qa/master-data/06-batch-detail-validated.png`
- `output/gui-qa/master-data/07-batch-detail-csv-package.png`
- `output/gui-qa/master-data/08-batch-detail-load-plan.png`
- `output/gui-qa/master-data/09-quality-tools-hub.png`
- `output/gui-qa/master-data/10-lat-lon-validator.png`
- `output/gui-qa/master-data/11-lat-lon-batch-detail.png`
- `output/gui-qa/master-data/12-lat-lon-export.png`

Validation not run:

- Fresh browser screenshots. Existing Master Data route-family browser evidence
  remains accepted visual evidence for #203; any future screenshot capture must
  first pass the `/api/v1/platform/navigation` runtime freshness gate.

Open risks:

- Direct OTM submission remains guarded/future scope until connection,
  credential, capability, audit, retry/job, and Oracle transport governance
  exist.
- Deeper audited spreadsheet editing, advanced coordinate diagnostics, backend
  retire/delete mutation, and deeper Load Plan handoff behavior remain backlog.
- Parallel shell/assistant and Integration Mapping work remains outside this
  closure.

Recommended next step:

Close #203 after push. Keep #202 open as the Master Data stabilization lane
until the next concrete follow-up slices are created or explicitly deferred.

## 2026-05-28 Order Release Revalidation

Status:
Revalidation complete; implementation follow-up required.

Scope:
Opened the Order Release stabilization lane (#204), revalidated Order Release
Generator against the active To-Be route-level workflow (#205), and created the
required implementation follow-up (#206).

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/ORDER_RELEASE_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -q`
  passed with 23 tests.
- `python -m pytest tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py -q`
  passed with 8 tests.
- `python -m pytest tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q`
  passed with 4 tests.
- `npm test -- src/app/AppFunctionalOrderReleaseGenerator.test.tsx` passed
  with 3 tests.
- `npm test -- src/app/App.test.tsx -t "Order Release"` passed with 1 test and
  29 skipped tests.
- `npm run build` passed with the existing Vite large chunk warning.

Validation not run:

- Fresh browser screenshots. The current result is not a visual acceptance
  claim; it records a route-level To-Be implementation gap.

Open risks:

- The current Order Release frontend is technically healthy but still a single
  staged workspace.
- To-Be acceptance requires route-level template and batch workflows with
  dedicated preview, artifacts, and submit-readiness routes.
- Submit-to-OTM must remain guarded until connection, credential, capability,
  audit, retry/job, and Oracle transport governance exist.

Recommended next step:

Close #205 after push. Continue #204 through #206:
`[Slice]: Order Release route-level template and batch workflows`.

## 2026-05-28 Order Release Route-Level Workflows

Status:
Implemented and validated, with browser QA blocked before module entry.

Scope:
Implemented #206 by making the current Order Release Generator frontend
route-aware for template and batch workflow destinations.

Files intentionally changed:

- `frontend/src/modules/order-release-generator/OrderReleaseGeneratorView.tsx`
- `frontend/src/app/AppFunctionalOrderReleaseGenerator.test.tsx`
- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_ROUTE_LEVEL_WORKFLOWS.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm test -- src/app/AppFunctionalOrderReleaseGenerator.test.tsx` passed with
  4 tests.
- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q`
  passed with 35 tests.
- `npm test -- src/app/App.test.tsx -t "Order Release"` passed with 1 test and
  29 skipped tests.
- `npm run build` passed with the existing Vite large chunk warning.

Validation not run / blocked:

- `npm run qa:functional:order-release:browser` was attempted and failed before
  reaching the module, timing out while waiting for `Project Cockpit`. Treat
  this as a local runtime/script entry issue, not module acceptance evidence.

Evidence:

- Direct URL recovery is covered by
  `AppFunctionalOrderReleaseGenerator.test.tsx`, including
  `/order-release-generator/batches/or_batch_1/preview`, route destination
  links, artifacts route, and submit-readiness route.

Open risks:

- This slice makes the To-Be URLs addressable and recoverable, but it does not
  fully redesign the visual layout into separate page components.
- Browser QA should be rerun after a fresh backend/frontend runtime is started.

Recommended next step:

Close #206 after push if the PR accepts automated coverage plus the recorded
browser-script limitation. Keep #204 open until a browser QA rerun or explicit
Order Release acceptance closeout.

## 2026-05-28 Load Plan Revalidation

Status:
Revalidation complete; implementation follow-up required.

Scope:
Opened the Load Plan stabilization lane (#207), revalidated Load Plan / Cutover
against the active package/checklist lifecycle (#208), and created the required
implementation follow-up (#209).

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_LOAD_PLAN_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/LOAD_PLAN_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_load_plan_package_intake.py -q` passed with 23
  tests.
- `python -m pytest tests/test_load_plan_cutover_checklist.py -q` passed with
  13 tests.
- `python -m pytest tests/test_load_plan_cutover_readiness.py -q` passed with
  9 tests.
- `python -m pytest tests/test_load_plan_csvutil_builder.py -q` passed with 16
  tests.
- `python -m pytest tests/test_load_plan_zip_analysis.py -q` passed with 12
  tests.
- `python -m pytest tests/test_load_plan_sequence_blockers.py -q` passed with
  13 tests.
- `python -m pytest tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py -q`
  passed with 16 tests.
- `python -m pytest tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_readiness_export.py -q`
  passed with 25 tests.
- `npm test -- src/app/AppFunctionalLoadPlan.test.tsx` passed with 1 test.
- `npm test -- src/app/App.test.tsx -t "Load Plan"` passed with 1 test and 29
  skipped tests.
- `npm run build` passed with the existing Vite large chunk warning.

Validation not run:

- Fresh browser screenshots. This revalidation does not claim visual
  acceptance; #209 must use the runtime navigation freshness gate before any
  browser evidence.

Open risks:

- Load Plan is technically healthy, but the frontend still uses a staged local
  workspace rather than route-level package operation recovery.
- Handoff must remain backend-owned and eligibility-gated.
- Protected `OTM_RESOURCES/` and unrelated dirty worktree changes remain out
  of scope.

Recommended next step:

Close #208 after push. Continue #207 through #209:
`[Slice]: Load Plan route-level package workflows`.

## 2026-05-28 Load Plan Route-Level Workflows

Status:
Implemented and validated, with browser QA deferred.

Scope:
Implemented #209 by making the current Load Plan frontend route-aware for
package operation destinations.

Files intentionally changed:

- `frontend/src/modules/load-plan/LoadPlanView.tsx`
- `frontend/src/app/AppFunctionalLoadPlan.test.tsx`
- `docs/agent/TASK_CONTRACT_LOAD_PLAN_ROUTE_LEVEL_WORKFLOWS.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `npm test -- src/app/AppFunctionalLoadPlan.test.tsx` passed with 2 tests.
- `npm test -- src/app/App.test.tsx -t "Load Plan"` passed with 1 test and 29
  skipped tests.
- `python -m pytest tests/test_load_plan_package_intake.py -q` passed with 23
  tests.
- `python -m pytest tests/test_load_plan_cutover_checklist.py -q` passed with
  13 tests.
- `python -m pytest tests/test_load_plan_cutover_readiness.py -q` passed with
  9 tests.
- `python -m pytest tests/test_load_plan_csvutil_builder.py -q` passed with 16
  tests.
- `python -m pytest tests/test_load_plan_zip_analysis.py -q` passed with 12
  tests.
- `python -m pytest tests/test_load_plan_sequence_blockers.py -q` passed with
  13 tests.
- `python -m pytest tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py -q`
  passed with 16 tests.
- `python -m pytest tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_readiness_export.py -q`
  passed with 25 tests.
- `npm run build` passed with the existing Vite large chunk warning.

Validation not run:

- Fresh browser screenshots. Browser QA must first pass the runtime navigation
  freshness gate.

Evidence:

- Direct URL recovery is covered by `AppFunctionalLoadPlan.test.tsx` for
  `/load-plan/packages/package_2/zip-review`, route destination links, and
  handoff route recovery.

Open risks:

- This slice makes the To-Be URLs addressable and recoverable, but it does not
  fully redesign the visual layout into separate page components.
- Go/no-go and handoff currently share the guarded handoff panel.

Recommended next step:

Close #209 after push if the PR accepts automated coverage plus deferred
browser visual evidence. Keep #207 open until Load Plan browser QA or explicit
Load Plan acceptance closeout.

## 2026-05-28 Load Plan Browser Closeout

Status:
Implemented, validated, and ready to close #207.

Scope:
Completed the Load Plan stabilization lane closeout with fresh runtime browser
QA.

Files intentionally changed:

- `frontend/scripts/functional-load-plan-browser.mjs`
- `migrations/versions/c5b9d3a1e6f2_load_plan_package_domain_scope.py`
- `docs/agent/TASK_CONTRACT_LOAD_PLAN_BROWSER_CLOSEOUT_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_modules_navigation.py -q` passed with 10 tests.
- Live `/api/v1/platform/navigation` on `http://127.0.0.1:8052` returned:
  `master_data`, `home`, `rates`, `load_plan`, `assets`,
  `order_release_generator`, `integration_mapping`, `settings`.
- `python -m alembic upgrade c5b9d3a1e6f2` passed on
  `var/qa-load-plan-route-closeout.db`.
- `npm run qa:functional:load-plan:browser` passed against backend
  `http://127.0.0.1:8052` and frontend `http://127.0.0.1:5222`.

Evidence:

- `var/qa/load-plan-route-closeout.png`

Validation not run:

- Full repository backend/frontend suites were not rerun in this closeout; #208
  and #209 already recorded focused automated coverage and GitHub Actions
  passed after the route recovery commit.

Open risks:

- The screenshot was captured from the shared dirty local workspace and includes
  a floating Assistant control from parallel work. The sidebar/module evidence
  remains valid because excluded top-level modules are absent.
- Deeper visual decomposition into separate Load Plan page components remains
  future enhancement, not current closeout scope.

Recommended next step:

Close #207 after push. The next roadmap lane can move to Assets backlog,
Settings/Cockpit context-isolation work, or another user-prioritized module.

## 2026-05-28 Assets Detail And Archive Impact Contracts

Status:
Implemented, validated, and ready to close #198.

Scope:
Added route-optimized Assets contracts so detail/archive screens use
backend-owned facts instead of frontend-only inference.

Files intentionally changed:

- `src/otm_workbench/modules/assets/assets.py`
- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `frontend/src/platform/types/assets.ts`
- `frontend/src/platform/hooks/assets.ts`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `docs/agent/TASK_CONTRACT_ASSETS_ROUTE_OPTIMIZED_DETAIL_ARCHIVE_IMPACT.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "route_optimized_detail or archive_impact or archive_asset_preserves" -q`
  passed with 3 tests.
- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "archives an asset on a direct route"`
  passed with 1 test.
- `python -m pytest tests/test_assets_library_assets.py -q` passed with 26
  tests.
- `npm test -- src/app/AppFunctionalAssets.test.tsx` passed with 13 tests.
- `npm run build` passed with the existing Vite large chunk warning.

Validation not run:

- Browser screenshot evidence. This slice changed API contracts and focused
  archive route consumption, not visual acceptance.

Evidence:

- Backend route detail no longer exposes version `storage_path`.
- Archive route invalidates detail/archive-impact/version/link queries after
  archive.

Open risks:

- The full Assets visual route decomposition remains future work.
- #199 and #200 remain open for backend-owned batch/checklist targets and OTM
  version taxonomy validation.

Next-chat intake notes:

- Treat Integration Mapping as reserved for its separate workstream.
- Use GitHub issue #199 or #200 as the next Assets step if continuing this lane.

Recommended next step:

Push the #198 commit, close #198, then continue with #199 unless the user
prioritizes Settings/Cockpit context-isolation first.

## 2026-05-28 Assets Batch And Checklist Link Targets

Status:
Implemented, validated, and ready to close #199.

Scope:
Added backend-owned BATCH and CHECKLIST link target validation for Assets.

Files intentionally changed:

- `src/otm_workbench/modules/assets/classifications.py`
- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `docs/agent/TASK_CONTRACT_ASSETS_BATCH_CHECKLIST_LINK_TARGETS.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "batch_and_checklist_link_targets" -q`
  passed with 2 tests.
- `python -m pytest tests/test_assets_library_assets.py -q` passed with 28
  tests.
- `python -m pytest tests/test_modules_navigation.py -q` passed with 10 tests.

Validation not run:

- Frontend/browser visual QA. This slice only added backend target validation
  and classification seeding.

Evidence:

- BATCH targets resolve only to scoped `LoadPlanPackage` rows.
- CHECKLIST targets resolve only when their parent package is scoped to the
  active user context.
- Hidden package/checklist rejections do not echo private target IDs or labels.

Open risks:

- BATCH currently means the Load Plan package contract in this UI phase. Future
  independent batch route families should introduce explicit backend target
  rules instead of frontend inference.
- #200 remains open for target OTM version taxonomy validation.

Next-chat intake notes:

- Treat Integration Mapping as reserved for its separate workstream.
- Use #200 as the next Assets backlog item if continuing the Assets lane.

Recommended next step:

Push the #199 commit, close #199, then continue with #200 or switch to
Settings/Cockpit context-isolation if prioritized.

## 2026-05-28 Assets Target OTM Version Taxonomy

Status:
Implemented, validated, and ready to close #200.

Scope:
Added backend-owned `target_otm_version` validation through an Assets
classification taxonomy.

Files intentionally changed:

- `src/otm_workbench/modules/assets/assets.py`
- `src/otm_workbench/modules/assets/classifications.py`
- `tests/test_assets_library_assets.py`
- `docs/agent/TASK_CONTRACT_ASSETS_TARGET_OTM_VERSION_TAXONOMY.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_assets_library_assets.py -k "target_otm_version" -q`
  passed with 2 tests.
- `python -m pytest tests/test_assets_library_assets.py -q` passed with 29
  tests.
- `python -m pytest tests/test_modules_navigation.py -q` passed with 10 tests.

Validation not run:

- Frontend/browser visual QA. This slice only changed backend taxonomy
  validation and governance documentation.

Evidence:

- `target_otm_version` accepts seeded `26A`/`26B` labels.
- Unsupported values such as `27A` are rejected on create and update without
  customer-specific release data.
- Decision recorded in `docs/agent/DECISION_LOG.md`.

Open risks:

- Future Oracle releases require governed classification additions after the
  relevant Oracle documentation baseline is confirmed.

Next-chat intake notes:

- Treat Integration Mapping as reserved for its separate workstream.
- Assets backlog issues #198, #199, and #200 are ready to be closed after this
  commit is pushed.

Recommended next step:

Push the #200 commit, close #200, then reassess the next roadmap lane outside
Assets backlog.

## 2026-05-28 Context Isolation Validation Matrix

Status:
Complete. Implemented, validated, merged through PR #182, and issue #214 is
closed.

Scope:
Opened the context-isolation foundation lane and documented the current
validation matrix across active UI phase modules.

Files intentionally changed:

- `docs/agent/TASK_CONTRACT_CONTEXT_ISOLATION_VALIDATION_MATRIX.md`
- `docs/agent/CONTEXT_ISOLATION_VALIDATION_MATRIX.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_operational_context.py -q` passed with 26 tests.
- `python -m pytest tests/test_modules_navigation.py -q` passed with 10 tests.

Validation not run:

- Browser screenshots. This slice records the backend/governance foundation and
  module-facing validation gates only.

Evidence:

- Platform context foundation is covered by `tests/test_operational_context.py`.
- Current UI phase navigation remains guarded by `tests/test_modules_navigation.py`.
- Module-specific gaps are recorded in
  `docs/agent/CONTEXT_ISOLATION_VALIDATION_MATRIX.md`.

Open risks:

- Cockpit, Rates, Master Data, and Order Release module-specific
  context-isolation evidence was later completed and recorded in subsequent
  handoff capsules.
- Integration Mapping remains reserved for its separate workstream.

Next-chat intake notes:

- Read `docs/agent/CONTEXT_ISOLATION_VALIDATION_MATRIX.md` before starting the
  next module lane.
- Create the next implementation issue only for the selected module/follow-up,
  not for every matrix gap at once.

Recommended next step:

Continue from `origin/main` with the next roadmap lane; do not reopen #214.

## 2026-05-28 Cockpit Context Selector Evidence

Status:
Complete. Implemented, validated, merged through PR #182, and issue #215 is
closed.

Scope:
Captured Cockpit context selector and route recovery evidence with a fresh
runtime navigation gate.

Files intentionally changed:

- `frontend/scripts/functional-shell-browser.mjs`
- `docs/agent/TASK_CONTRACT_COCKPIT_CONTEXT_SELECTOR_EVIDENCE.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q`
  passed with 17 tests.
- `npm test -- src/app/App.test.tsx -t "Cockpit"` passed with 1 selected test.
- `node --check scripts/functional-shell-browser.mjs` passed.
- `npm run qa:functional:shell:browser` passed against backend
  `http://127.0.0.1:8054` and frontend `http://127.0.0.1:5232`.
- `npm run build` passed with the existing Vite large chunk warning.

Evidence:

- Live navigation IDs before browser QA: `master_data`, `home`, `rates`,
  `load_plan`, `assets`, `order_release_generator`, `integration_mapping`,
  `settings`.
- Screenshot: `var/qa/cockpit-context-selector.png`.

Validation not run:

- Full frontend functional suite. This slice changed only the shell browser QA
  script and evidence docs.

Open risks:

- The screenshot includes the floating Assistant launcher from unrelated local
  dirty work. The sidebar and Cockpit context evidence are valid because
  excluded top-level modules are absent.
- Cockpit still needs deeper user-review/visual acceptance before being marked
  complete.

Next-chat intake notes:

- Do not use `VITE_API_BASE_URL` for local browser QA unless backend CORS is
  explicitly configured; use `VITE_DEV_PROXY_TARGET` for the Vite dev server.
- Integration Mapping remains reserved for its separate workstream.

Recommended next step:

Continue from `origin/main` with the next roadmap lane; do not reopen #215.

## 2026-05-28 PR 182 Merge Conflict Recovery

Status:
Complete. Conflicts resolved in an isolated worktree, backend plus frontend
validation passed, PR #182 was pushed, marked ready for review, and merged
into `main`.

GitHub tracking:

- Issue #220: PR #182 merge-conflict recovery.
- Issue #220 closed after merge recovery.
- PR #182: merged into `main` on 2026-05-28.
- PR #182 merge commit: `0594b5d67d3d8cc3b97dff489c2675214ffc49df`.
- Issue #225: follow-up handoff state sync, closed through PR #226.
- PR #226: merged with commit `07456c35f17b10ba70899e877386daab3eedc36d`.

Files intentionally changed:

- Merge resolution across docs, backend, frontend, migrations, and tests from
  `origin/main` into `codex/master-data-catalog-redesign-evidence`.
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_modules_navigation.py tests/test_operational_context.py -q`
  passed with 35 tests.
- `python -m pytest tests/test_project_cockpit_summary.py tests/test_rates_batches.py -q`
  passed with 17 tests.
- `python -m pytest tests/test_master_data_templates.py -k "same_name or active_context_scope or dba_context" -q`
  passed with 4 selected tests.
- `python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -k "same_name or active_context_scope or dba_context" -q`
  passed with 8 selected tests.
- `python -m pytest tests/test_assets_library_assets.py -q` passed with 29
  tests when `OTM_OTM_DATA_DICTIONARY_ROOT` pointed at the local
  `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict` directory.
- `npm test -- src/app/AppFunctionalAssets.test.tsx src/app/AppFunctionalShell.test.tsx`
  passed with 2 files and 15 tests.
- `npm run build` passed with the existing Vite large chunk warning.
- GitHub PR #182 Backend CI, Frontend CI/build, and CodeRabbit passed before
  merge.

Validation not run:

- Browser screenshots; this slice is merge recovery and does not intentionally
  change visible UI behavior.
- Full all-module pytest sweep; an initial broad command timed out, then the
  touched surfaces were split into focused passing suites.

Open risks:

- `OTM_RESOURCES` remains local/untracked by policy. Isolated worktrees still
  need the Data Dictionary path explicitly configured.

Next-chat intake notes:

- Do not stage the primary workspace's broad dirty state.
- Integration Mapping changes present in this merge came from `origin/main`;
  do not extend that module in this chat beyond merge preservation.

Recommended next step:

Continue with the next roadmap lane from `origin/main`; do not reopen #225.

## 2026-05-28 OTM_RESOURCES Versioning Policy

Status:
Complete. Issue #221 was implemented, PR #222 was merged into `main`, and the
resource policy is now active.

GitHub tracking:

- Issue #221: OTM_RESOURCES versioning and sensitivity policy.
- PR #222: merged.
- Issue #223: follow-up handoff state sync, closed through PR #224.
- PR #224: merged with commit `28e0d2d8fb97d91c0a9884248b67c58dfdc72e3c`.

Files intentionally changed:

- `.gitignore`
- `.env.example`
- `docs/agent/OTM_RESOURCES_VERSIONING_POLICY.md`
- `docs/agent/TASK_CONTRACT_OTM_RESOURCES_VERSIONING_POLICY.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `tests/test_rates_dictionary.py`
- `tests/test_rates_batch_csv_preview.py`
- `tests/test_rates_batch_scenarios.py`
- `tests/test_rates_csv_preview.py`

Validation run:

- `git check-ignore -v` confirmed `OTM_RESOURCES/` and `*.db.xml` paths are
  ignored.
- Initial `tests/test_rates_dictionary.py tests/test_modules_navigation.py`
  run failed with 3 rates dictionary failures because tests still used a
  hardcoded local Data Dictionary path.
- Final `python -m pytest tests/test_rates_dictionary.py tests/test_rates_batch_csv_preview.py tests/test_rates_batch_scenarios.py tests/test_rates_csv_preview.py tests/test_modules_navigation.py -q`
  passed with 37 tests when `OTM_OTM_DATA_DICTIONARY_ROOT` pointed at the local
  Data Dictionary.
- `git diff --check` passed.
- GitHub PR #222 Backend CI, Frontend CI/build, and CodeRabbit passed before
  merge.

Validation not run:

- Browser screenshots; this is repository governance and test configuration
  policy, not a UI behavior change.

Evidence:

- GitHub repository visibility is public.
- Local resource inventory found Data Dictionary reference files,
  operator/operand spreadsheets, and `*.db.xml` exports.
- Raw resource files were not copied into this branch.
- Initial backend validation exposed low-level rates tests with hardcoded
  Data Dictionary paths; those tests now use `get_settings()`.

Open risks:

- Data Dictionary and XLS resources may still be useful for CI or clean
  worktrees, but public versioning requires license/provenance review.
- Contributors need to configure `OTM_OTM_DATA_DICTIONARY_ROOT` locally until a
  governed private artifact or sanitized fixture path exists.

Next-chat intake notes:

- Do not add raw `OTM_RESOURCES` content in this slice.
- `OTM_OTM_DATA_DICTIONARY_ROOT` is still required for local clean worktrees
  that run Data Dictionary-dependent tests.

Recommended next step:

Continue with the next roadmap lane from `origin/main`; do not reopen #223.

## 2026-05-28 Frontend Route Inventory Guard

Status:
Complete. Issue #229 was implemented, PR #230 was merged into `main`, and the
route inventory guard is now active.

GitHub tracking:

- Issue #229: frontend route inventory guard, closed.
- PR #230: merged with commit `12c700a4a4f059c98b355fb6fdba5ae51805c378`.
- Issue #231: follow-up handoff state sync.

Files intentionally changed:

- `frontend/src/app/routes/WorkbenchRoute.test.tsx`
- `docs/agent/FRONTEND_ROUTE_INVENTORY.md`
- `docs/agent/TASK_CONTRACT_FRONTEND_ROUTE_INVENTORY_GUARD.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `python -m pytest tests/test_modules_navigation.py -q` passed with 9 tests.
- `npm test -- src/app/routes/WorkbenchRoute.test.tsx src/app/shell/SidebarNav.test.tsx`
  passed with 2 files and 8 tests.
- `git diff --check` passed.
- GitHub PR #230 Backend CI, Frontend CI/build, and CodeRabbit passed before
  merge.

Validation not run:

- Browser screenshots; this slice does not intentionally change visible UI
  behavior.

Evidence:

- Backend navigation already guards the current UI phase module set in
  `tests/test_modules_navigation.py`.
- New frontend test verifies excluded direct routes do not render unless the
  backend navigation contract exposes them.

Open risks:

- Excluded route source files still exist and are classified rather than
  removed. Removal needs a separate cleanup slice.
- Integration Mapping remains reserved for its dedicated workstream.

Next-chat intake notes:

- Do not delete route components in this guard slice.

Recommended next step:

Close issue #231 after this handoff sync is committed and merged, then continue
with the next frontend cleanup lane from `origin/main`.

## 2026-05-28 Frontend Cleanup Candidate Classification

Status:
Implemented and ready for PR on branch `codex/frontend-cleanup-classification`.

GitHub tracking:

- Issue #233: Governance: classify frontend cleanup candidates.

Scope:
Created the non-destructive cleanup classification layer that converts the
current route inventory into reviewable keep/hide/absorb/alter/archive/remove
or create decisions before source cleanup.

Files intentionally changed:

- `docs/agent/FRONTEND_CLEANUP_CANDIDATE_CLASSIFICATION.md`
- `docs/agent/TASK_CONTRACT_FRONTEND_CLEANUP_CLASSIFICATION.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

Validation run:

- `git diff --check` passed.

Validation not run:

- Backend, frontend, and browser QA are not required unless this docs-only
  classification changes behavior.

Open risks:

- Cleanup candidates are classification only. Future deletion, archive, or
  route removal still needs a separate issue, explicit file list, tests, and
  user approval where appropriate.

Recommended next step:

Run `git diff --check`, open a PR, and close #233 after merge.
