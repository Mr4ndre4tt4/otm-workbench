# Validation Report

**Status:** completed for FigJam as-is solution diagnostics documentation sync
**Date:** 2026-05-27

## 2026-05-28 Assets Acceptance Pass Validation

Validation intent:

- complete issue #197 by accepting or deferring current Assets scope;
- avoid adding product behavior during an acceptance/reporting slice;
- keep future backlog visible in GitHub.

Validation performed:

```powershell
GitHub CLI: issue create #198 #199 #200
GitHub CLI: issue edit #195
GitHub CLI: issue comment #197
git diff --cached --check
```

Results:

```text
Assets acceptance checklist created.
Backlog issues #198, #199, and #200 created under milestone Assets.
Version issue #195 updated with child and backlog links.
```

Validation evidence reused from #196:

```text
Assets backend suite: 50 passed.
Assets functional suite: 13 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed after live navigation freshness gate.
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings.
```

Validation not run:

- full repository backend suite;
- full repository frontend suite;
- new browser QA.

Reason:
This slice is an acceptance and backlog closeout report only. It does not change
runtime behavior.
## 2026-05-28 Assets Target OTM Version Search Validation

Validation intent:

- implement issue #196 with a backend-owned `target_otm_version` contract;
- prove backend create/update/list/search behavior with TDD;
- expose the UI filter only after backend tests pass;
- capture browser QA only after live navigation freshness is verified.

Validation performed:

```powershell
python -m pytest tests/test_assets_library_assets.py -k "target_otm_version or table_exists" -q
python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py -q
npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
python -m alembic heads
npm run qa:functional:assets:browser
```

Results:

```text
Focused backend target OTM version test: failed before implementation, then 2 passed.
Assets backend suite: 50 passed.
Focused frontend Assets journey: failed before UI control, then 1 passed / 12 skipped.
Assets functional suite: 13 passed.
Frontend build: passed with existing Vite large chunk warning.
Alembic head: c1f4a8e7d9b2.
Browser QA: passed.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8025
Frontend: http://127.0.0.1:5204
Database: var/qa-assets-target-otm-version.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Existing Assets screenshots refreshed by the browser journey, including
var/qa/assets-library-search.png.
```

Validation not run:

- full repository backend suite;
- full repository frontend suite.

Reason:
This slice is constrained to Assets target OTM version metadata/search.
## 2026-05-28 Assets Version Train Setup Validation

Validation intent:

- create a GitHub-visible Assets version train before the next implementation
  slice;
- use existing GitHub milestones and small child issues;
- avoid touching product code or Integration Mapping.

Validation performed:

```powershell
C:\Program Files\GitHub CLI\gh.exe issue list --repo Mr4ndre4tt4/otm-workbench --state open --limit 60 --json number,title,labels,milestone,updatedAt,url
C:\Program Files\GitHub CLI\gh.exe api repos/Mr4ndre4tt4/otm-workbench/milestones --paginate
C:\Program Files\GitHub CLI\gh.exe issue create/edit/comment ...
```

Results:

```text
Issue #195 created for v0.3-assets-stabilization under milestone Assets.
Issues #196 and #197 created as child delivery slices.
Issue #194 and PR #182 updated with the operational follow-up.
```

Validation not run:

- backend tests;
- frontend tests;
- browser QA.

Reason:
This is GitHub delivery-tracking work only.
## 2026-05-28 GitHub Versioning And Issue Cadence Validation

Validation intent:

- document a lightweight GitHub versioning and issue cadence workflow;
- create the first GitHub governance issue for the cadence change;
- avoid mixing unrelated local Assistant or Integration Mapping work into this
  governance commit.

Validation performed:

```powershell
GitHub connector: create issue #194
Documentation diff review
git diff --cached --check
```

Results:

```text
GitHub issue #194 created: Govern GitHub versioning cadence and smaller delivery issues.
Documentation-only governance change; no runtime behavior changed.
```

Validation not run:

- backend tests;
- frontend tests;
- browser QA.

Reason:
This slice only changes delivery governance and documentation.
## 2026-05-28 Assets Linked Target Search UI Validation

Validation intent:

- expose the backend-owned `linked target type` filter on `/assets/library`;
- keep Storybook optional and unused for this small in-context form extension;
- verify browser QA on a fresh backend/frontend runtime.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
```

Results:

```text
Focused long Assets journey: 1 passed, 12 skipped after the expected red
failure was fixed.
Assets functional suite: 13 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8024
Frontend: http://127.0.0.1:5203
Database: var/qa-assets-linked-target-ui.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Existing Assets screenshots refreshed by the browser journey, including
var/qa/assets-library-search.png.
```

Validated:

- `Asset linked target type filter` is rendered from asset link
  classifications;
- `Asset linked target type operator` supports `one_of` and `not_one_of`;
- applying search sends `linked_target_type` and
  `linked_target_type_operator`;
- reset search clears linked target type and restores `one_of`;
- live navigation evidence stayed inside the current UI phase.

Deferred:

- target OTM version search remains a future slice.

## 2026-05-28 Assets Linked Target Search API Validation

Validation intent:

- add backend-owned filtering for the Assets Library `linked target type`
  metadata field;
- preserve existing list filters, pagination, and scoping behavior;
- avoid frontend or Integration Mapping implementation changes.

Validation performed:

```powershell
python -m pytest tests/test_assets_library_assets.py -k "linked_target_type"
python -m pytest tests/test_assets_library_assets.py
python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py
```

Results:

```text
Focused linked target type tests: 2 passed, 21 deselected.
Assets backend suite: 23 passed.
Explicit Assets Library file list: 49 passed.
```

Validated:

- `linked_target_type=module` returns only assets linked with `MODULE`;
- `linked_target_type_operator=one_of` accepts comma-separated link types;
- `linked_target_type_operator=not_one_of` excludes matching linked assets and
  retains unlinked assets;
- unsupported linked target operators return `ASSET_SEARCH_INVALID_OPERATOR`;
- existing asset list, permission, foundation, link, and version behavior
  remains covered.

Deferred:

- frontend linked target type filter UI;
- target OTM version search.

## 2026-05-28 Assets Library Row Actions Validation

Validation intent:

- expose route-level row actions from `/assets/library`;
- preserve the existing in-page selected-asset workflow;
- verify browser QA on a fresh backend/frontend runtime.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "library row actions"
npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
```

Results:

```text
Focused row actions test: 1 passed, 12 skipped after the expected red failure
was fixed.
Focused long Assets journey: 1 passed, 12 skipped.
Assets functional suite: 13 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8023
Frontend: http://127.0.0.1:5202
Database: var/qa-assets-row-actions.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Existing Assets screenshots refreshed by the browser journey, including
var/qa/assets-library-search.png.
```

Validated:

- search result rows expose `Open <asset>`, `Upload version for <asset>`, and
  `Archive <asset>` links;
- result rows still expose `Select <asset>` for the existing in-page workflow;
- create, edit, version, link, download, archive, and return flows still pass;
- live navigation evidence stayed inside the current UI phase.

Deferred:

- linked target type and target OTM version search remain future slices.

## 2026-05-28 Assets Library Search UI Validation

Validation intent:

- connect `/assets/library` to the backend-owned search/operator/pagination
  contract;
- prove the UI sends text operator params and page-size params;
- capture browser QA evidence on a fresh backend/frontend runtime.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
```

Results:

```text
Focused Assets journey test: 1 passed, 11 skipped after the expected red
failure was fixed.
Assets functional suite: 12 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8022
Frontend: http://127.0.0.1:5201
Database: var/qa-assets-search-ui.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Search screenshot: var/qa/assets-library-search.png
```

Validated:

- `Apply search` sends backend-owned query params for `name`,
  `name_operator`, `description`, `description_operator`, module/macro/table
  operators, and `page_size`;
- `Reset search` clears text/filter values and restores default `contains`
  operators plus page size 50;
- pagination metadata is visible as `Showing ... of ... assets`;
- route-level create, edit, version, link, download, archive, and return flows
  still pass in the Assets browser journey;
- live navigation evidence stayed inside the current UI phase.

Deferred:

- linked target type and target OTM version search remain future slices.

## 2026-05-27 Assets Library Search API Validation

Validation intent:

- start the backend-owned search/operator/pagination contract for
  `/api/v1/modules/assets/assets`;
- preserve the existing exact filters while adding operator-based metadata
  search;
- align permissions tests with the active-context scoping rule.

Validation performed:

```powershell
python -m pytest tests/test_assets_library_assets.py -k "backend_search_operators or pagination_metadata or invalid_search_operator"
python -m pytest tests/test_assets_library_assets.py
python -m pytest tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py
python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py
```

Results:

```text
Before implementation: 3 failed as expected because the endpoint ignored the new
operator/pagination params.
After implementation: 3 passed, 18 deselected.
Assets backend suite: 21 passed.
Assets permissions/foundation: 9 passed.
Explicit Assets Library file list: 47 passed.
```

Non-result:

```text
python -m pytest tests/test_assets_library_*.py
```

PowerShell did not expand the glob, so pytest collected 0 tests and reported the
path missing. The explicit file-list command above replaced it.

Validated:

- pagination returns bounded `items`, full filtered `total`, `page`, and
  `page_size`;
- search operators support case-insensitive `contains` and `begins_with`;
- `one_of` and `not_one_of` support comma-separated values;
- invalid operators return `ASSET_SEARCH_INVALID_OPERATOR`;
- existing asset list filters and scope behavior remain covered;
- non-admin users without active context cannot read operational assets.

Deferred:

- frontend search-builder UI for `/assets/library`;
- browser QA, because this slice changed backend/API behavior only and has no
  new visible UI state yet.

Scope coordination:

Integration Mapping is reserved for a separate dedicated chat/workstream unless
the user explicitly asks for it, the current chat is already in Integration
Mapping context, or a minimal cross-module adjustment is required.

## 2026-05-27 Assets Detail Actions Cleanup

Validation intent:

- align `/assets/:assetId` route-level actions with the consolidated Assets
  spec;
- add missing upload, download, and archive actions to the detail screen;
- keep download guarded by the existing backend endpoint.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
node scripts/functional-assets-browser.mjs
git diff --check
```

Results:

```text
Focused asset detail route test: 1 passed.
Assets functional suite: 12 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8021
Frontend: http://127.0.0.1:5199
Database: var/qa-assets-detail-actions.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Detail actions screenshot: var/qa/assets-detail-actions-route.png
```

Validated:

- `/assets/:assetId` exposes `Edit metadata`, `Upload version`, `View versions`,
  `Manage links`, `Download current version`, and `Archive asset`;
- `Download current version` calls the existing backend guarded download
  endpoint and does not expose local file paths;
- `Archive asset` routes to the existing archive confirmation screen;
- browser QA checks the detail actions before archive and then completes the
  existing archive/switch/return journey;
- live navigation evidence stayed inside the current UI phase.

Deferred:

- `/assets/:assetId/download` review route remains optional because the spec
  allows direct guarded backend download.
- Backend-owned search operators/pagination for `/assets/library`.

## 2026-05-27 Assets Acceptance Create Route Cleanup

Validation intent:

- close the first Assets acceptance gap after classifications route extraction;
- make `/assets/new` a route-level create screen;
- remove classification authoring from asset creation so classification changes
  stay under `/assets/classifications/*`.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "dedicated route without classification authoring"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
node scripts/functional-assets-browser.mjs
git diff --check
```

Results:

```text
Focused create-route acceptance test: 1 passed.
Assets functional suite: 12 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8020
Frontend: http://127.0.0.1:5198
Database: var/qa-assets-create-route.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Asset create screenshot: var/qa/assets-create-route.png
Classification screenshots:
  var/qa/assets-classifications-route.png
  var/qa/assets-classification-create-route.png
  var/qa/assets-classification-edit-route.png
```

Validated:

- `/assets/new` renders a route-level create task without the temporary Assets
  Library workflow rail;
- the create route starts from the default synthetic asset draft, not the
  selected or first asset in the library;
- asset creation no longer renders `Asset classification authoring`;
- classification creation remains available through the dedicated
  classifications routes;
- the existing asset lifecycle journey remains green after route-level create,
  workflow edit, direct edit, version upload/history, links, archive, switch,
  and return checks;
- live browser navigation evidence stayed inside the current UI phase and did
  not show excluded top-level modules.

Deferred:

- Backend-owned search operators/pagination for `/assets/library`.
- Optional create-and-upload flow.
- `/assets/:assetId/download` guarded review route if later required.

## 2026-05-27 Assets Classifications Routes Slice

Validation intent:

- continue Assets route extraction after archive review;
- add route-level classification list, create, and edit screens;
- keep classification authoring separated from asset creation while preserving
  the legacy create-stage bridge for compatibility.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset classification"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
node scripts/functional-assets-browser.mjs
```

Results:

```text
Focused asset classification route tests: 3 passed.
Assets functional suite: 11 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8019
Frontend: http://127.0.0.1:5197
Database: var/qa-assets-classifications-routes.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Classification list screenshot:   var/qa/assets-classifications-route.png
Classification create screenshot: var/qa/assets-classification-create-route.png
Classification edit screenshot:   var/qa/assets-classification-edit-route.png
```

Validated:

- `/assets/classifications` renders classification groups without the temporary
  Assets Library workflow rail;
- `/assets/classifications/new` creates a classification through the existing
  backend contract;
- `/assets/classifications/:classificationId/edit` patches editable fields
  through the existing backend contract;
- system-protected classifications are guarded from route-level editing;
- the live browser navigation contract stayed inside the current UI phase:
  no Catalog Core, Evidence Hub, Admin Console, Developer Tools, or Coordinate
  Quality top-level module appeared in acceptance evidence;
- the existing asset create, workflow edit, direct edit, direct versions, direct
  links, archive, switch, and return journey remains green.

Notes:

- An initial browser QA attempt against frontend `5196` was invalid because
  `VITE_API_BASE_URL` caused direct CORS preflight to backend `8019`. The valid
  evidence is from frontend `5197` using `VITE_DEV_PROXY_TARGET`.
- `var/qa-assets-classifications-routes.db` was cloned from the previous valid
  archive QA database because local Alembic reads `alembic.ini` for its URL.

## 2026-05-27 Assets Archive Route Slice

Validation intent:

- continue Assets route extraction after link management;
- add archive confirmation at `/assets/:assetId/archive`;
- keep archive eligibility backend-owned while using existing asset/version/link
  data for impact summary.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "archives an asset"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

Results:

```text
Focused asset archive route test: 1 passed.
Assets functional suite: 8 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8018
Frontend: http://127.0.0.1:5195
Database: var/qa-assets-archive-route.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Archive screenshot: var/qa/assets-archive-route.png
```

Validated:

- `/assets/:assetId/archive` renders without the temporary Assets Library
  workflow rail;
- `Archive asset` calls the existing backend archive endpoint;
- the archive impact screen shows the current file, current version id, version
  count, linked target count, and archived state after mutation;
- the existing create, workflow edit, direct edit, direct versions, direct
  links, workflow links, download, archive guards, switch, and return journey
  remains green.

## 2026-05-27 Assets Links Route Slice

Validation intent:

- continue Assets route extraction after version history/upload;
- add relationship management at `/assets/:assetId/links`;
- keep archive review, classification refinement, and backend target lookup
  improvements outside this slice.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset link"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

Results:

```text
Focused asset links route test: 1 passed.
Assets functional suite: 7 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8017
Frontend: http://127.0.0.1:5194
Database: var/qa-assets-links-route.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Links screenshot: var/qa/assets-links-route.png
```

Validated:

- `/assets/:assetId/links` renders without the temporary Assets Library
  workflow rail;
- the direct route creates a `MODULE` link through the existing backend
  contract;
- the route exposes `Back to Asset` and `Back to Library`;
- the existing create, workflow edit, direct edit, direct versions, workflow
  links, download, archive, switch, and return journey remains green.

## 2026-05-27 Assets Versions Routes Slice

Validation intent:

- continue Assets route extraction after metadata edit;
- add version history at `/assets/:assetId/versions`;
- add direct version upload at `/assets/:assetId/versions/new`;
- keep link management, classification management, and archive review outside
  this slice.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset versions route"
npm test -- src/app/AppFunctionalAssets.test.tsx -t "uploads an asset version on a direct route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

Results:

```text
Focused asset versions route test: 1 passed.
Focused direct upload route test: 1 passed.
Assets functional suite: 6 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8016
Frontend: http://127.0.0.1:5192
Database: var/qa-assets-versions-routes.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Version history screenshot: var/qa/assets-versions-route.png
Version upload screenshot:  var/qa/assets-version-upload-route.png
```

Validated:

- `/assets/:assetId/versions` renders without the temporary Assets Library
  workflow rail;
- `/assets/:assetId/versions/new` uploads a new file version through the
  existing backend contract;
- version history exposes `Back to Asset`, `Back to Library`, `Upload new
  version`, and guarded `Download current version`;
- the existing create, workflow edit, direct edit, link, download, archive,
  switch, and return journey remains green.

## 2026-05-27 Assets Edit Metadata Route Slice

Validation intent:

- continue Assets route extraction after the direct detail route;
- add metadata-only editing at `/assets/:assetId/edit`;
- keep version upload, link management, lifecycle/archive, and classifications
  out of the metadata screen.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "edits asset metadata"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

Results:

```text
Focused asset edit route test: 1 passed.
Assets functional suite: 4 passed.
Frontend build: passed with existing Vite large chunk warning.
Browser QA: passed.
git diff --check: no errors, LF/CRLF warnings only.
```

Browser QA environment:

```text
Backend:  http://127.0.0.1:8015
Frontend: http://127.0.0.1:5191
Database: var/qa-assets-edit-metadata-route.db
User:     demo@example.test
```

Browser QA evidence:

```text
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
Detail screenshot: var/qa/assets-detail-route.png
Edit screenshot:   var/qa/assets-edit-metadata-route.png
```

Validated:

- `/assets/:assetId/edit` renders without the temporary Assets Library workflow
  rail;
- `Save metadata` patches the asset and keeps the user on the direct edit
  screen with success feedback;
- `Back to Asset` and `Back to Library` are visible;
- the existing create, workflow edit, upload, link, download, archive, switch,
  and return journey remains green.

## 2026-05-27 Assets Detail Route Slice

Validation intent:

- continue Assets route extraction after the hub/library split;
- add direct asset inspection at `/assets/:assetId`;
- preserve the existing `/assets/library` functional workflow.

Validation performed:

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
python -m pytest tests/test_assets_library_assets.py::test_create_draft_asset_records_metadata_audit_and_event -q
git diff --check
```

Results:

```text
Focused asset detail route test: 1 passed.
Assets functional suite: 3 passed.
Frontend build: passed with existing Vite large chunk warning.
Backend asset create smoke: 1 passed.
git diff --check: no errors; existing LF/CRLF warnings only.
```

Browser QA:

```text
npm run qa:functional:assets:browser
```

Initial result:

```text
Blocked before reaching the new detail route. The existing local backend on
http://127.0.0.1:8000 returned HTTP 500 while the browser script seeded an
asset through POST /api/v1/modules/assets/assets. The source-level backend
asset create smoke passed in pytest, so this is recorded as a local runtime
freshness/database issue rather than a failed asset-detail implementation.
```

Root cause and fix:

```text
The default local database `var/otm_workbench.db` was stale and lacked the
current Assets scope columns, which caused the original 500. A fresh QA runtime
then exposed a real scoped-create bug: the frontend creates assets without
explicit project/environment/domain fields, and the backend did not inherit the
active context, so the created row became hidden from its own detail/update
routes. Assets create now merges missing scope fields from the active context.
```

Additional validation:

```powershell
python -m pytest tests/test_assets_library_assets.py -q
npm run qa:functional:assets:browser
```

Final result:

```text
Assets backend suite: 18 passed.
Browser QA passed against:
- Backend: http://127.0.0.1:8014
- Frontend: http://127.0.0.1:5190
- Database: var/qa-assets-detail-route-2.db
- Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
- Screenshot: var/qa/assets-detail-route.png
```

Browser-script hardening:

- added a live `/api/v1/platform/navigation` stale-module check before browser
  QA proceeds;
- added synthetic evidence/artifact seeding so Assets link QA no longer
  depends on residual evidence in a reused database;
- extended the script to visit `/assets/:assetId` and capture
  `var/qa/assets-detail-route.png`.

## 2026-05-27 CodeRabbit Governance Update

Validation intent:

- add CodeRabbit to the governance model without making it a premature merge
  gate;
- add repository-level CodeRabbit configuration;
- keep protected local resources and generated evidence out of review scope.

Validation performed:

```powershell
rg -n "CodeRabbit|GitHub CLI|branch protection|delivery visibility|GITHUB_DELIVERY|coderabbit" AGENTS.md docs\agent docs\otm-workbench .github -S
python -m pytest tests/test_modules_navigation.py -q
npm test -- src/app/AppFunctionalShell.test.tsx
```

External documentation checked:

- CodeRabbit documents that `.coderabbit.yaml` belongs in the repository root.
- CodeRabbit supports `path_filters` and `path_instructions` for scoped review.
- CodeRabbit distinguishes path instructions from general code guidelines.

Validation not performed:

- CodeRabbit CLI review was not run because `coderabbit` is not installed in
  the current terminal.

Result:

CodeRabbit is documented as optional assistive review. `.coderabbit.yaml` was
added with draft PR auto-review disabled, local/protected artifacts excluded,
and path-specific review guidance.

Smoke validation:

```text
Backend navigation guard: 9 passed.
Frontend shell functional smoke: 1 file passed, 1 test passed.
```

## 2026-05-27 GitHub Operating Setup Follow-Up

Validation intent:

- complete the practical GitHub setup after installing GitHub CLI;
- configure labels and milestones for the new workflow;
- inspect the first CI failures;
- adjust CI to the current representative suite instead of the full historical
  test suite.

Result:

```text
GitHub CLI: gh version 2.92.0, authenticated as Mr4ndre4tt4.
Labels: created/confirmed.
Milestones: created/confirmed.
Issues #183-#187: labeled and assigned to phase milestones.
Initial CI runs: failed because the first workflow used full backend/frontend
historical suites. Backend full suite expects protected local OTM_RESOURCES and
paused/historical surfaces; frontend full suite includes legacy/current-scope
contract mismatches.
Workflow correction: `.github/workflows/ci.yml` now runs the representative
current governance/UI phase suite that does not require protected local
`OTM_RESOURCES/`.
```

Validation commands:

```powershell
python -m pytest tests/test_modules_navigation.py tests/test_operational_context.py tests/test_project_cockpit_summary.py tests/test_rates_batches.py tests/test_assets_library_assets.py -q
npm test -- src/app/AppFunctionalAssets.test.tsx src/app/AppFunctionalRates.test.tsx src/app/AppFunctionalShell.test.tsx
npm run build
```

Validation results:

```text
Backend representative suite with local Assets/Data Dictionary coverage:
67 passed in 196.31s.
Frontend functional suite: 3 files passed, 7 tests passed.
Frontend build: passed.
```

CI note:

The first corrected backend CI run still failed because
`tests/test_assets_library_assets.py` indirectly depends on local protected Data
Dictionary resources. The CI backend gate was narrowed to tests that can run in
a clean GitHub runner. Assets backend coverage should return to CI after a
committed synthetic Data Dictionary fixture or fixture shim exists.

Build note:

Vite reported the existing large chunk warning after successful build.

## 2026-05-27 GitHub Governance Migration

Validation intent:

- make GitHub the active delivery visibility layer;
- keep durable decisions in repo docs;
- add lightweight PR/Issue templates and CI;
- mark Linear as historical/paused without deleting historical evidence.

Validation performed:

```powershell
git status --short --branch
rg -n "Linear|GitHub|DELIVERY_PIPELINE|visibility board|board" AGENTS.md docs .github -S
python -m pytest tests/test_modules_navigation.py -q
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
```

Result:

Docs and GitHub repository controls were updated.

```text
Backend navigation guard: 9 passed.
Frontend shell functional smoke: 1 file passed, 1 test passed.
Frontend build: passed.
```

Build note:

Vite reported the existing large chunk warning after successful build. This is
not a governance migration blocker.

## 2026-05-27 GitHub Recovery Checkpoint

Validation intent:

- publish the accumulated local work to GitHub in reviewable commits;
- exclude protected local resources under `OTM_RESOURCES/`;
- verify representative backend and frontend behavior before push;
- report any validation that cannot be completed.

Validation commands planned:

```powershell
pytest tests/test_modules_navigation.py tests/test_operational_context.py tests/test_project_cockpit_summary.py tests/test_rates_batches.py tests/test_assets_library_assets.py -q
npm test -- src/app/AppFunctionalAssets.test.tsx src/app/AppFunctionalRates.test.tsx src/app/AppFunctionalShell.test.tsx
npm run build
```

Results:

```text
Backend representative suite: 67 passed.
Frontend functional suite: 3 files passed, 7 tests passed.
Frontend build: passed.
```

Build note:

Vite reported a large chunk warning after successful build. This is not a
checkpoint blocker, but future frontend performance work can consider code
splitting.

## 2026-05-27 Chat Continuity Workflow Guardrail

Validation performed:

- analyzed context-loss risks between chats, including compressed memory,
  stale screenshots, dirty worktree ambiguity, lost plugin/tool state, partial
  implementation attempts, missing handoff notes, and docs/code disagreement;
- created `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`;
- linked the workflow from `AGENTS.md`, delivery pipeline, change control,
  decision log, risk register, handoff, validation report, and document
  inventory;
- added a new risk entry for chat context loss;
- added a required previous-chat handoff capsule and new-chat intake gate.

Validation not performed:

- backend tests;
- frontend tests;
- browser QA.

Reason:

This was a documentation-only governance guardrail. It changed process rules,
not runtime behavior.

Remaining risks:

- Future chats must still follow the workflow. The mitigation is to expose it
  from the main agent entry point and required governance controls.

## 2026-05-27 Runtime Freshness Incident And Guardrail

Validation performed:

- investigated why an Assets browser screenshot showed excluded top-level
  modules in the sidebar;
- confirmed source navigation is whitelist-driven and excludes Catalog Core,
  Evidence Hub, separate Admin Console, Developer Tools, and other out-of-phase
  top-level modules;
- confirmed `tests/test_modules_navigation.py` covers both exclusion and
  current-phase ordering;
- identified the local backend on port `8000` as a stale non-reload `uvicorn`
  process;
- restarted the backend and re-queried live navigation;
- updated governance docs so future screenshots require runtime freshness
  verification before acceptance.

Commands:

```powershell
pytest tests/test_modules_navigation.py -q
npm test -- src/app/AppFunctionalAssets.test.tsx
```

Results:

```text
tests/test_modules_navigation.py: 9 passed
AppFunctionalAssets.test.tsx: 2 passed
live demo navigation after restart:
master_data, home, rates, load_plan, assets, order_release_generator,
integration_mapping
```

Validation not performed:

- no full backend regression;
- no full frontend suite;
- no new acceptance screenshot was captured after the documentation-only
  guardrail update.

Reason:

This task changed governance and validation rules. The stale-runtime cause was
already isolated, and the relevant navigation plus Assets functional checks
passed.

Remaining risks:

- Any already-captured screenshot from before the runtime restart should be
  treated as suspect if it shows excluded sidebar modules.
- Future browser QA must record backend/frontend URLs and the navigation
  freshness result before screenshot evidence is accepted.

## 2026-05-27 Context Segregation Backend QA

Validation performed:

- verified Public View/shared-data behavior stays explicit and narrow;
- verified Integration Mapping child mapping create/list/detail/delete guards
  for non-DBA users without active context;
- verified Master Data batch action guards for non-DBA users without active
  context;
- verified Load Plan package child/action/update guards for non-DBA users
  without active context;
- re-ran targeted context-scope smoke tests for Master Data and Load Plan.

Commands:

```powershell
pytest tests/test_operational_metadata.py::test_platform_public_artifact_makes_public_scope_explicit tests/test_operational_metadata.py::test_platform_public_evidence_without_artifact_makes_public_scope_explicit tests/test_order_release_generator_foundation.py::test_order_release_templates_keep_public_seed_but_hide_private_without_active_context_for_non_admin -q
pytest tests/test_integration_mapping_mappings.py::test_integration_mapping_child_routes_require_active_context_for_non_admin -q
pytest tests/test_integration_mapping_definitions.py tests/test_integration_mapping_systems.py tests/test_integration_mapping_mappings.py -q
pytest tests/test_master_data_templates.py::test_master_data_batches_require_active_context_for_non_admin_access_and_create -q
pytest tests/test_master_data_templates.py::test_master_data_batches_follow_active_context_scope tests/test_master_data_templates.py::test_master_data_batches_require_active_context_for_non_admin_access_and_create tests/test_master_data_templates.py::test_master_data_dba_context_can_see_all_domains_in_active_environment -q
pytest tests/test_load_plan_package_intake.py::test_load_plan_packages_require_active_context_for_non_admin_access_and_register -q
pytest tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail_follow_active_context_scope tests/test_load_plan_package_intake.py::test_load_plan_packages_require_active_context_for_non_admin_access_and_register tests/test_load_plan_package_intake.py::test_load_plan_package_dba_context_can_see_all_domains_in_active_environment -q
git diff --check -- tests\test_integration_mapping_mappings.py tests\test_master_data_templates.py tests\test_load_plan_package_intake.py docs\superpowers\plans\2026-05-27-context-segregation-foundation.md docs\agent\HANDOFF.md docs\agent\VALIDATION_REPORT.md
```

Results:

```text
Public/shared scope targeted tests: 3 passed.
Integration Mapping targeted child CRUD guard: 1 passed.
Integration Mapping route suite: 33 passed.
Master Data no-context action guard: 1 passed.
Master Data scope/no-context/DBA smoke: 3 passed.
Load Plan no-context action guard: 1 passed.
Load Plan scope/no-context/DBA smoke: 3 passed.
```

Validation not performed:

- full backend regression;
- frontend tests;
- browser QA.

Reason:

This slice extended backend access-control tests and documentation only. No
frontend behavior changed.

Remaining risks:

- Settings frontend completion gates and policy-binding UX still need their own
  implementation and browser QA slice.
- Future module-specific fixture slices must still create valid large synthetic
  files only where the scenario requires them.

## 2026-05-27 Synthetic Fixture Baseline

Validation performed:

- created baseline synthetic fixtures under `tests/fixtures/synthetic/`;
- covered CSV, XML, JSON, XSLT, PDF, DOCX, MD, XLSX, and ZIP formats;
- validated the OTM-shaped `RATE_GEO_COST` CSV shape and date session line;
- validated the `RATE_GEO_COST` CSV columns against the local OTM 26B Data
  Dictionary JSON file;
- validated XML/XSLT parsing, JSON parsing, XLSX workbook loading, DOCX ZIP
  container structure, PDF header/footer, and ZIP contents.

Command:

```powershell
pytest tests/test_synthetic_fixtures.py -q
```

Result:

```text
5 passed.
```

Validation not performed:

- no browser QA;
- no module-specific large/performance fixture generation;
- no official Oracle documentation lookup for functional behavior.

Reason:

This slice created the baseline fixture pack and a fixture-integrity test. It
did not implement or change a module workflow. Official Oracle documentation
remains a required gate when a module-specific scenario has technical or
functional uncertainty beyond the local Data Dictionary.

## 2026-05-27 Context Segregation Final Targeted Verification

Validation performed:

- re-ran the synthetic fixture integrity suite;
- re-ran public/shared scope tests;
- re-ran representative Integration Mapping, Master Data, and Load Plan
  no-active-context action guards;
- ran `git diff --check` across the context-guard tests, fixture pack, and
  documentation touched by this slice.

Command:

```powershell
pytest tests/test_synthetic_fixtures.py tests/test_operational_metadata.py::test_platform_public_artifact_makes_public_scope_explicit tests/test_operational_metadata.py::test_platform_public_evidence_without_artifact_makes_public_scope_explicit tests/test_order_release_generator_foundation.py::test_order_release_templates_keep_public_seed_but_hide_private_without_active_context_for_non_admin tests/test_integration_mapping_mappings.py::test_integration_mapping_child_routes_require_active_context_for_non_admin tests/test_master_data_templates.py::test_master_data_batches_require_active_context_for_non_admin_access_and_create tests/test_load_plan_package_intake.py::test_load_plan_packages_require_active_context_for_non_admin_access_and_register -q
git diff --check -- tests\test_synthetic_fixtures.py tests\fixtures\synthetic tests\test_integration_mapping_mappings.py tests\test_master_data_templates.py tests\test_load_plan_package_intake.py docs\agent\TEST_SCENARIO_FIXTURE_STRATEGY.md docs\agent\VALIDATION_REPORT.md docs\agent\HANDOFF.md docs\superpowers\plans\2026-05-27-context-segregation-foundation.md
```

Result:

```text
11 passed.
git diff --check completed without errors.
```

Validation not performed:

- full backend regression;
- frontend tests;
- browser QA.

Reason:

This was a backend test and documentation/fixture slice. No frontend behavior
changed, and no browser-facing module surface was completed in this step.

## 2026-05-27 Master Data Generated Scope Inheritance

Validation performed:

- updated Master Data CSV package export so generated ZIP artifact, manifest,
  and evidence inherit project/profile, environment, domain, and `PROJECT`
  visibility from the source `MasterDataBatch`;
- extended the CSV package export test to create the batch under active context
  and assert generated artifact, manifest, and evidence scope;
- re-ran export, retry/idempotency, and artifact/download smoke coverage.

Command:

```powershell
pytest tests/test_master_data_templates.py::test_master_data_batch_export_csv_package_creates_zip_manifest_and_evidence tests/test_master_data_templates.py::test_master_data_batch_export_csv_package_is_idempotent_for_retry tests/test_master_data_templates.py::test_master_data_batch_detail_and_artifacts_are_client_safe_and_downloadable -q
```

Result:

```text
3 passed.
```

Validation not performed:

- full Master Data test suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-record scope inheritance only.

## 2026-05-27 Integration Mapping Generated Scope Inheritance

Validation performed:

- updated Integration Mapping payload sample, preview, and generated markdown
  spec artifacts so they inherit project/profile, environment, domain, and
  `PROJECT` visibility from the source `IntegrationDefinition`;
- extended one test per artifact generator to create the definition under
  active context and assert inherited artifact scope;
- re-ran the payload artifact, preview, and spec generator suites.

Command:

```powershell
pytest tests/test_integration_mapping_payload_artifacts.py tests/test_integration_mapping_preview.py tests/test_integration_mapping_spec_generator.py -q
```

Result:

```text
26 passed.
```

Validation not performed:

- full Integration Mapping suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-artifact scope inheritance only.

## 2026-05-27 Load Plan Package Intake Scope Inheritance

Validation performed:

- updated Rates package intake evidence to inherit project/profile,
  environment, domain, and `PROJECT` visibility from the source `RateBatch`;
- updated Master Data package intake so the `LoadPlanPackage`, intake evidence,
  and package-registered domain event inherit the source `MasterDataBatch`
  project/domain boundary;
- extended package-intake tests for Rates and Master Data scope inheritance and
  idempotency.

Command:

```powershell
pytest tests/test_load_plan_package_intake.py::test_register_rates_package_creates_client_safe_evidence_audit_and_event tests/test_load_plan_package_intake.py::test_register_master_data_package_creates_load_plan_package tests/test_load_plan_package_intake.py::test_register_master_data_package_creates_client_safe_evidence_audit_and_event tests/test_load_plan_package_intake.py::test_register_master_data_package_is_idempotent -q
```

Result:

```text
4 passed.
```

Validation not performed:

- full Load Plan suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend package/evidence scope inheritance only.

## 2026-05-27 Load Plan Cutover Package Scope Inheritance

Validation performed:

- updated cutover checklist readiness evidence to derive domain from the
  registered `LoadPlanPackage` and preserve project/profile/environment;
- verified cutover checklist creation evidence carries package scope;
- verified cutover package export artifact, manifest, and evidence carry
  package/checklist scope;
- verified go/no-go decision evidence carries package/checklist scope.

Command:

```powershell
pytest tests/test_load_plan_cutover_checklist.py::test_create_cutover_checklist_from_load_plan_package tests/test_load_plan_cutover_checklist.py::test_cutover_checklist_readiness_reports_blockers tests/test_load_plan_cutover_package_export.py::test_cutover_package_export_creates_client_safe_zip tests/test_load_plan_cutover_go_no_go.py::test_cutover_go_no_go_returns_no_go_without_export_package tests/test_load_plan_cutover_go_no_go.py::test_cutover_go_no_go_returns_go_after_export_package -q
pytest tests/test_load_plan_cutover_checklist.py tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py -q
git diff --check -- src/otm_workbench/modules/load_plan/cutover_checklist.py src/otm_workbench/modules/load_plan/cutover_package.py src/otm_workbench/modules/load_plan/cutover_go_no_go.py tests/test_load_plan_cutover_checklist.py tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py docs/superpowers/plans/2026-05-27-context-segregation-foundation.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

Result:

```text
Targeted scope tests: 5 passed.
Cutover checklist/package/go-no-go suite: 18 passed.
git diff --check completed without errors.
```

Validation not performed:

- full Load Plan suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-record scope inheritance only.

## 2026-05-27 Order Release XML Artifact Scope Inheritance

Validation performed:

- updated generated Order Release XML artifacts to explicitly carry
  `PROJECT` visibility with batch project/profile/environment/domain scope;
- updated generated Order Release XML evidence to explicitly carry the same
  batch scope;
- added end-to-end coverage for batch creation, XML artifact generation,
  evidence lookup, and artifact listing under active context.

Commands:

```powershell
pytest tests/test_order_release_generator_batches.py::test_order_release_xml_artifact_inherits_batch_scope -q
pytest tests/test_order_release_generator_batches.py -q
```

Result:

```text
Targeted XML scope test: 1 passed.
Order Release batch suite: 10 passed.
```

Validation not performed:

- full Order Release suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-artifact/evidence scope inheritance only.

## 2026-05-27 Rates Approval Evidence Scope Inheritance

Validation performed:

- updated Rates approval evidence to explicitly carry `PROJECT` visibility with
  batch project/profile/environment/domain scope;
- added coverage for approval evidence generated after CSV preview;
- re-ran the Rates CSV export/artifact suite to keep export, evidence, latest
  export, download, and approval behavior together.

Commands:

```powershell
pytest tests/test_rates_csv_export_artifacts.py::test_rate_batch_approval_evidence_inherits_batch_scope -q
pytest tests/test_rates_csv_export_artifacts.py -q
```

Result:

```text
Targeted approval scope test: 1 passed.
Rates CSV export/artifact suite: 11 passed.
```

Validation not performed:

- full Rates suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-evidence scope inheritance only.

## 2026-05-27 Load Plan Sequence Snapshot Scope Inheritance

Validation performed:

- updated Load Plan sequence snapshot evidence to explicitly carry `PROJECT`
  visibility with package project/profile/environment/domain scope;
- extended the existing Load Plan active-context route test to assert visible
  sequence evidence scope while hidden sequence snapshots remain inaccessible.

Command:

```powershell
pytest tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail_follow_active_context_scope -q
```

Result:

```text
1 passed.
```

Validation not performed:

- full Load Plan suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-evidence scope inheritance only.

## 2026-05-27 Load Plan Review Decision Scope Inheritance

Validation performed:

- updated Load Plan review decision evidence to explicitly carry `PROJECT`
  visibility with review-item project/profile/environment scope and package
  domain;
- added audit/event payload scope metadata for review decisions;
- extended review decision tests to assert evidence, decision, audit, and
  event scope.

Commands:

```powershell
pytest tests/test_load_plan_review_decisions.py::test_review_decision_updates_item_and_creates_evidence_audit_event -q
pytest tests/test_load_plan_review_decisions.py -q
```

Result:

```text
Targeted review decision scope test: 1 passed.
Load Plan review decision suite: 7 passed.
```

Validation not performed:

- full Load Plan suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated-evidence scope inheritance only.

## 2026-05-27 Master Data Template Workbook Public Scope

Validation performed:

- updated published Master Data template workbook artifacts to explicitly carry
  `domain_name=PUBLIC` and `visibility=PUBLIC`;
- verified generated workbooks remain client-safe and template download remains
  bound to the matching template code/version.

Command:

```powershell
pytest tests/test_master_data_templates.py::test_master_data_template_build_workbook_creates_artifact tests/test_master_data_templates.py::test_master_data_template_workbook_download_is_client_safe_and_scoped -q
```

Result:

```text
2 passed.
```

Validation not performed:

- full Master Data suite;
- frontend tests;
- browser QA.

Reason:

This slice changed backend generated shared-artifact scope metadata only.

## 2026-05-27 Task 4 Generated Artifact Scope Closure

Validation performed:

- audited `Artifact`, `Manifest`, and `Evidence` construction across active
  modules and platform shared paths;
- confirmed active UI phase generators now either inherit private operational
  scope from their source record or declare explicit public shared scope;
- closed Task 4 in the context-segregation plan for active modules;
- documented Coordinate Quality export as the remaining `needs-review`
  exception because its parent batch model has no operational scope fields and
  the utility is outside top-level UI scope for this phase.

Command:

```powershell
rg -n "Artifact\(|Manifest\(|Evidence\(" src/otm_workbench/modules src/otm_workbench/evidence_hub src/otm_workbench/platform -g "*.py"
rg -n "visibility=|domain_name=|project_id=|profile_id=|environment_id=" src/otm_workbench/modules/load_plan src/otm_workbench/modules/master_data src/otm_workbench/modules/rates src/otm_workbench/modules/order_release_generator src/otm_workbench/modules/integration_mapping src/otm_workbench/evidence_hub src/otm_workbench/platform -g "*.py"
```

Result:

```text
Active module generated artifacts/evidence are covered by explicit private
scope inheritance or explicit PUBLIC scope.
Coordinate Quality export remains the only known generator exception and is
tracked as needs-review before scope migration.
```

Validation not performed:

- no full backend regression;
- no frontend tests;
- no browser QA.

Reason:

This was a documentation/governance closure based on backend constructor audit.

## 2026-05-27 Task 5 Settings Scope Authority Closure

Validation performed:

- confirmed the Settings backend tests and module navigation tests pass;
- confirmed the Settings frontend test path passes through the existing
  `AdminConsoleView` component;
- verified the component name remains preserved in the route and export;
- closed Task 5 in the context-segregation plan.

Commands:

```powershell
pytest tests/test_operational_context.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Settings"
rg -n "AdminConsoleView" frontend/src/modules/admin/AdminConsoleView.tsx frontend/src/app/routes/WorkbenchRoute.tsx frontend/src/app/App.test.tsx
```

Result:

```text
Operational context/navigation tests: 35 passed.
Frontend Settings test: 1 passed, 27 skipped by test filter.
AdminConsoleView export and WorkbenchRoute usage remain in place.
```

Validation not performed:

- full backend regression;
- full frontend suite;
- browser QA.

Reason:

This slice closed the Settings governance task using the expected Task 5
validation commands and did not change runtime code.

## 2026-05-27 Task 6 Operational Module Guard Closure

Validation performed:

- re-ran Cockpit summary and module navigation coverage;
- re-ran representative active-context guard coverage across Rates, Load Plan,
  Assets, Master Data, Integration, and Order Release;
- closed Task 6 in the context-segregation plan.

Commands:

```powershell
pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q
pytest tests/test_rates_csv_export_artifacts.py::test_rate_batch_approval_evidence_inherits_batch_scope tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail_follow_active_context_scope tests/test_assets_library_assets.py::test_asset_routes_follow_active_context_scope tests/test_master_data_templates.py::test_master_data_batches_follow_active_context_scope tests/test_integration_mapping_definitions.py::test_integration_definitions_follow_active_context_scope tests/test_order_release_generator_batches.py::test_order_release_batches_follow_active_context_scope -q
```

Result:

```text
Cockpit/navigation tests: 15 passed.
Representative operational module guard tests: 6 passed.
```

Validation note:

```text
An earlier representative command used an outdated Assets test name and ran no
tests. The corrected command above passed.
```

Validation not performed:

- full backend regression;
- frontend tests;
- browser QA.

Reason:

This slice closed the operational module guard governance task with targeted
backend validation and did not change runtime code.

## 2026-05-27 Context Segregation Plan Closure Sync

Validation performed:

- updated Task 8 status to reflect completed Tasks 1-8 for the active UI phase;
- updated handoff recommendations so Settings/Cockpit scope authority is no
  longer listed as an open context-segregation item;
- kept remaining work framed as future module completion slices with
  task-specific fixtures, browser QA, and tracking updates.

Command:

```powershell
git diff --check -- docs/superpowers/plans/2026-05-27-context-segregation-foundation.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

Result:

```text
git diff --check completed without errors.
```

Validation not performed:

- backend tests;
- frontend tests;
- browser QA.

Reason:

This slice synchronized documentation after already-passed Task 5 and Task 6
validation. No runtime behavior changed.

## 2026-05-27 FigJam As-Is Solution Diagnostics

Validation performed:

- inspected governance docs, architecture map, module scope ledger, and module
  documentation index;
- inspected backend package, route registrations, SQLAlchemy model groups,
  frontend package, and frontend route/module structure;
- identified the open Figma team from Chrome:

```text
team: otm-workbench
team id: 1631369663740377053
```

- generated the FigJam board:

```text
OTM Workbench - Stack As-Is Map
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

- generated eight diagrams into the same FigJam file:

```text
OTM Workbench - Stack As-Is Map
OTM Workbench - UI Scope Boundary
OTM Workbench - Module Implementation Matrix
OTM Workbench - Backend Frontend DB By Module
OTM Workbench - Operational Flow As-Is To Target
OTM Workbench - Cleanup Decision Flow
OTM Workbench - Function Status By Module
OTM Workbench - Core Data Model Overview
```

Validation not performed:

- backend tests;
- frontend tests;
- build;
- lint;
- browser QA against the local app.

Reason:

This slice created documentation and FigJam diagnostic artifacts only. No
source code, migrations, tests, or frontend implementation files were changed.

Remaining risks:

- The FigJam diagnostics still need user/Michelangelo review.
- Cleanup is not approved by the diagrams alone.
- Excluded top-level modules may still have backend/internal value and must be
  classified carefully before any route hiding or code removal.

## 2026-05-26 Project Cockpit v3 Penpot Creation And Cleanup

### Validation Performed

Command:

```powershell
Get-Content 'docs\agent\penpot-wireframes\PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json' -Raw | ConvertFrom-Json
```

Result:

```text
module: Shell / Project Cockpit v3
status: created in Penpot on 2026-05-26; old generated boards removed
targetPageName: 01C Shell Context Selector Cockpit v3
targetPageId: 575775e8-ca97-8021-8008-14ec4ed580d8
FrameCount: 4
```

### Penpot Validation

Readback from Penpot confirmed:

```text
file-id: e7a86fff-661d-81c1-8008-14af24af603d
file: otm-workbech-new-wireframe
page-id: 575775e8-ca97-8021-8008-14ec4ed580d8
page: 01C Shell Context Selector Cockpit v3
totalBoards: 4
v3Boards: 4
marker: project-cockpit-shell-v3
revision: v3-single-cockpit
```

Boards read back:

```text
SHELLV3-00 Navigation map | wireframe map | navigation-map | children=31
SHELLV3-01 Login | /login | unauthenticated | children=19
SHELLV3-02 Logout or session ended | /logout | signed-out | children=18
SHELLV3-03 Project Cockpit | /home | active-context | children=121
```

Old generated boards removed from Penpot:

```text
zz superseded empty - Project Cockpit v1: 14 generated SHELL-xx boards removed
zz superseded empty - Project Cockpit v2.1: 7 generated SHELLV2-xx boards removed
```

The plugin API does not expose direct page deletion, so old pages were renamed
as superseded empty pages instead of being removed.

### Documentation Validation

Additional module pair check:

```text
PROJECT_COCKPIT scope=True brief=True
MASTER_DATA_DATA_FACTORY scope=True brief=True
CATALOG_CORE scope=True brief=True
RATES_STUDIO scope=True brief=True
LOAD_PLAN_CUTOVER scope=True brief=True
EVIDENCE_HUB scope=True brief=True
ASSETS_LIBRARY scope=True brief=True
INTEGRATION_MAPPING_STUDIO scope=True brief=True
ORDER_RELEASE_GENERATOR scope=True brief=True
ADMIN_CONSOLE_JOBS scope=True brief=True
DEVELOPER_TOOLS scope=True brief=True
COORDINATE_QUALITY scope=True brief=True
```

### Validation Not Performed

Backend tests, frontend tests, build, lint, and browser QA were not run because
this slice changed documentation and Penpot wireframes only. No source code,
tests, migrations, or frontend implementation files were changed.

### Remaining Risks

- Project Cockpit v3 still needs user/Michelangelo visual review.
- Project Info secure vault behavior requires a separate security design before
  implementation.
- `DOCUMENT_INVENTORY.md` remains category-level and still needs a file-by-file
  pass.
- GitHub updates are deferred until product behavior or delivery slices
  change.

## 2026-05-27 Cockpit Deep Flow Completion

### Automated Validation

Commands:

```powershell
pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Cockpit"
npm test -- src/app/AppFunctionalShell.test.tsx
npm test -- src/app/App.test.tsx -t "unknown backend routes"
git diff --check -- src/otm_workbench/platform/routes.py tests/test_project_cockpit_summary.py frontend/src/platform/types/cockpit.ts frontend/src/app/routes/WorkbenchRoute.tsx frontend/src/app/App.test.tsx frontend/src/app/AppFunctionalShell.test.tsx frontend/src/app/shell/ContextSwitcher.tsx frontend/src/ui/layouts.css src/otm_workbench/platform/navigation.py docs/superpowers/plans/2026-05-27-cockpit-deep-flow-completion.md
```

Results:

```text
16 passed
App.test.tsx - Cockpit: 1 passed, 28 skipped by filter
AppFunctionalShell.test.tsx: 1 passed
App.test.tsx - unknown backend routes: 1 passed, 28 skipped by filter
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8012
Frontend: http://127.0.0.1:5178
Database: var/qa-cockpit-isolated.db
User:     demo@example.test
```

Evidence:

```text
var/qa/cockpit-public-view.png
var/qa/cockpit-private-scope-viewport.png
var/qa/cockpit-scoped-user.png
var/qa/cockpit-route-recovery.png
```

Validated:

- Public View state renders inside Context Selector; private accelerators are
  blocked with `ACTIVE_CONTEXT_REQUIRED`.
- Private client/domain context renders with project, profile, environment,
  and `OTM1` selected in the selector.
- Project Info shows secure-vault metadata only and does not show secrets.
- DBA visibility is explicit in Project Info.
- Normal-user restricted visibility shows `SCOPED` access and only the allowed
  `PUBLIC, OTM1` domain scope.
- Accelerators launch the module route; Rates Studio opened and navigation
  returned to Project Cockpit.
- Unknown routes render `Module unavailable` with a visible `Return to Cockpit`
  path.

Additional command:

```powershell
@' ... scoped Playwright QA ... '@ | node --input-type=module
```

Result:

```json
{
  "status": "passed",
  "screenshot": "var/qa/cockpit-scoped-user.png"
}
```

## 2026-05-27 Settings Policy Binding UX

### Automated Validation

Commands:

```powershell
pytest tests/test_operational_context.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check -- src/otm_workbench/platform/routes.py tests/test_operational_context.py frontend/src/platform/types/platform.ts frontend/src/modules/admin/AdminConsoleView.tsx frontend/src/app/App.test.tsx frontend/src/ui/layouts.css docs/agent/TASK_CONTRACT_SETTINGS_POLICY_BINDING_UX.md docs/superpowers/plans/2026-05-27-settings-policy-binding-ux.md
```

Results:

```text
26 passed
App.test.tsx - Settings: 1 passed, 28 skipped by filter
frontend build: passed
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8020
Frontend: http://127.0.0.1:5181
Database: var/qa-settings-policy.db
User:     demo@example.test
```

Evidence:

```text
var/qa/settings-policy-binding-review.png
```

Validated:

- Settings renders the access-policy binding review.
- The review shows backend-owned project, visibility, and domain requirements.
- The seeded private `OTM1` policy shows an active-context `READY` state.
- Vite QA uses the repo proxy target to avoid CORS-only failures.

## 2026-05-27 Settings Role And Grant Review UX

### Automated Validation

Commands:

```powershell
pytest tests/test_operational_context.py -q -k "project_setup_admin_can_author_roles_and_grants"
npm test -- src/app/App.test.tsx -t "Settings"
pytest tests/test_operational_context.py -q
npm run build
git diff --check -- src/otm_workbench/platform/routes.py tests/test_operational_context.py frontend/src/platform/types/platform.ts frontend/src/modules/admin/AdminConsoleView.tsx frontend/src/app/App.test.tsx frontend/src/ui/layouts.css docs/agent/TASK_CONTRACT_SETTINGS_ROLE_GRANT_REVIEW_UX.md docs/superpowers/plans/2026-05-27-settings-role-grant-review-ux.md
```

Results:

```text
Focused backend red/green: 1 passed, 25 deselected after implementation
App.test.tsx - Settings: 1 passed, 28 skipped by filter
Full operational context: 26 passed
frontend build: passed
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8021
Frontend: http://127.0.0.1:5182
Database: var/qa-settings-grant-review.db
User:     demo@example.test
```

Evidence:

```text
var/qa/settings-grant-binding-review.png
```

Validated:

- Settings renders the grant-binding review.
- The review shows backend-owned user, role, project, environment, and domain
  requirements.
- The seeded `OTM1` UAT grant shows an active-context `READY` state.

## 2026-05-27 Settings Setup Recovery UX

### Automated Validation

Commands:

```powershell
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check -- frontend/src/modules/admin/AdminConsoleView.tsx frontend/src/app/App.test.tsx frontend/src/ui/layouts.css docs/agent/TASK_CONTRACT_SETTINGS_SETUP_RECOVERY_UX.md docs/superpowers/plans/2026-05-27-settings-setup-recovery-ux.md
```

Results:

```text
App.test.tsx - Settings: 2 passed, 28 skipped by filter
frontend build: passed
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8022
Frontend: http://127.0.0.1:5183
Database: var/qa-settings-setup-recovery.db
User:     demo@example.test
```

Evidence:

```text
var/qa/settings-setup-recovery-empty.png
```

Validated:

- Settings renders setup recovery in an empty setup database.
- The recovery area shows backend-owned blocker/action state.
- The setup forms show compact empty selector states such as
  `Workspace required`, `Project required`, `Role required`, and
  `User required`.
- A visible `Return to Cockpit` link is present.

Follow-up found during QA:

- A normal non-admin user with no setup authority reaches `Settings is
  unavailable` because supporting audit/feature flag requests return `403`.
  This should be handled in a later Settings scoped-read hardening slice.

## 2026-05-27 Settings Final Revalidation

### Automated Validation

Commands:

```powershell
npm test -- src/app/App.test.tsx -t "Settings"
pytest tests/test_operational_context.py -q
npm run build
git diff --check -- docs/agent/TASK_CONTRACT_SETTINGS_FINAL_REVALIDATION.md docs/agent/module-revalidation/SETTINGS_FINAL_REVALIDATION_2026_05_27.md docs/agent/VALIDATION_REPORT.md docs/agent/HANDOFF.md
```

Results:

```text
App.test.tsx - Settings: 2 passed, 28 skipped by filter
Operational context: 26 passed
frontend build: passed
```

Decision:

```text
Settings is accepted for the current UI phase with non-blocking follow-ups.
Next module: Rates Studio completion against 10 / Rates Studio Deep Flow.
```

## 2026-05-27 Rates Route Recovery UX

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check -- frontend/src/modules/rates/RatesSummaryView.tsx frontend/src/app/AppFunctionalRates.test.tsx frontend/src/ui/layouts.css docs/agent/TASK_CONTRACT_RATES_ROUTE_RECOVERY_UX.md docs/superpowers/plans/2026-05-27-rates-route-recovery-ux.md
```

Results:

```text
AppFunctionalRates.test.tsx: 2 passed
frontend build: passed
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8023
Frontend: http://127.0.0.1:5184
Database: var/qa-rates-route-recovery.db
User:     demo@example.test
```

Evidence:

```text
var/qa/rates-route-recovery-lifecycle.png
```

Validated:

- `/rates` renders a lifecycle destination panel.
- `Back to Cockpit`, `Back to Rates`, `Open batch library`, and `Create rate
  batch` are visible.
- Selected-batch lifecycle links are deterministic from the selected batch id.
- Existing create, stage, preview, export, download, approve, and validate
  functional flows still pass.

## 2026-05-27 Rates Approval And Export Review UX

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check -- frontend/src/modules/rates/RatesSummaryView.tsx frontend/src/app/AppFunctionalRates.test.tsx frontend/src/ui/layouts.css docs/agent/TASK_CONTRACT_RATES_APPROVAL_EXPORT_REVIEW_UX.md docs/superpowers/plans/2026-05-27-rates-approval-export-review-ux.md
```

Results:

```text
AppFunctionalRates.test.tsx: 2 passed
frontend build: passed
git diff --check: no errors
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8024
Frontend: http://127.0.0.1:5185
Database: var/qa-rates-review-gates.db
User:     demo@example.test
```

Evidence:

```text
var/qa/rates-approval-export-review-gates.png
```

Validated:

- Approval confirmation includes a `Rate approval review` summary.
- CSV export opens a `Rate export review` summary before backend execution.
- `Confirm export` is required before calling the export endpoint.
- The backend-owned `export_csv` action path is also routed through the same
  review gate.

## 2026-05-27 Rates Batch Library Search UX

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
AppFunctionalRates.test.tsx: 2 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8026
Frontend: http://127.0.0.1:5187
Database: var/qa-rates-batch-library.db
User:     demo@example.test
```

Evidence:

```text
var/qa/rates-batch-library-search.png
```

Validated:

- `/rates` renders a `Rate batch library` panel backed by
  `GET /api/v1/modules/rates/batches`.
- Library filters cover free-text search, status, and domain.
- Filtered selection updates `Selected rate batch` without losing existing
  lifecycle destinations.
- Browser QA caught and fixed the compact list-contract case where batch list
  items do not include detail-only `tables`.

## 2026-05-27 Rates Route-Level Batch Screens

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
AppFunctionalRates.test.tsx: 3 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8027
Frontend: http://127.0.0.1:5188
Database: var/qa-rates-route-level.db
User:     demo@example.test
```

Evidence:

```text
var/qa/rates-route-level-batch-issues.png
```

Validated:

- Direct `/rates/batches/:batchId` recovery renders `Rate batch overview`.
- `Stage tables` route renders a route-level staging workflow and successfully
  stages a synthetic `X_LANE` row.
- `Review issues` route renders backend-owned validation issues from
  `/api/v1/modules/rates/batches/:batchId/issues`.
- Browser QA used a validated synthetic batch with 4 backend-generated issues.

## 2026-05-27 Rates Route-Level Review Screens

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
AppFunctionalRates.test.tsx: 3 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8028
Frontend: http://127.0.0.1:5189
Database: var/qa-rates-route-reviews.db
User:     demo@example.test
```

Evidence:

```text
var/qa/rates-route-level-review-screens.png
```

Validated:

- Direct `/rates/batches/:batchId/csv-preview` recovery renders
  `Rate CSV preview` and can generate preview output.
- Direct `/rates/batches/:batchId/export` recovery renders
  `Rate export review` and exports only after `Confirm export`.
- Direct `/rates/batches/:batchId/approve` recovery renders
  `Rate approval review` and approves only after an approval note.

## 2026-05-27 Rates Artifact Evidence Handoff Routes

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
AppFunctionalRates.test.tsx: 3 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8030
Frontend: http://127.0.0.1:5191
Database: var/qa-rates-artifact-evidence-handoff.db
User:     qa.rates@example.test
```

Evidence:

```text
var/qa/rates-artifact-evidence-handoff-routes.png
```

Validated:

- Direct `/rates/batches/:batchId/artifacts` recovery renders
  `Rate batch artifacts` and exposes the backend artifact download action.
- Direct `/rates/batches/:batchId/evidence` recovery renders
  `Rate batch evidence` with export and approval evidence records.
- Direct `/rates/batches/:batchId/load-plan` recovery renders
  `Rate Load Plan handoff` with batch, domain, catalog path, artifact count,
  and evidence count.
- `Register Load Plan package` posts to the existing Load Plan package intake
  endpoint and returns a registered package message.

## 2026-05-27 Rates Library And New Route Recovery

### Revalidation Finding

The Rates consolidated spec defines `/rates/batches` and `/rates/batches/new`
as first-class screens. Revalidation found that both URLs were linked from the
hub but still rendered generic hub behavior instead of route-specific screens.

### Automated Validation

Commands:

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
AppFunctionalRates.test.tsx: 4 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8031
Frontend: http://127.0.0.1:5192
Database: var/qa-rates-library-new-routes.db
User:     qa.rates@example.test
```

Evidence:

```text
var/qa/rates-library-new-routes.png
```

Validated:

- Direct `/rates/batches` renders `Rate batch library`.
- Search/filter UI remains usable on the route-level library screen.
- Direct `/rates/batches/new` renders `New rate batch` with `Back to batch library`.
- The new route avoids duplicate heading text by using `Batch setup` for the
  inner form panel.

## 2026-05-27 Rates Table Detail Route

### Automated Validation

Commands:

```powershell
pytest tests/test_rates_batches.py::test_rate_batch_table_detail_returns_rows_and_table_issues -q
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
test_rate_batch_table_detail_returns_rows_and_table_issues: passed
AppFunctionalRates.test.tsx: 4 passed
frontend build: passed
```

### Browser QA

Environment:

```text
Backend:  http://127.0.0.1:8032
Frontend: http://127.0.0.1:5193
Database: var/qa-rates-table-detail-route.db
User:     qa.rates@example.test
```

Evidence:

```text
var/qa/rates-table-detail-route.png
```

Validated:

- Batch overview table rows now link to
  `/rates/batches/:batchId/tables/:tableName`.
- Direct table detail route renders `Rate batch table detail`.
- The backend table-detail endpoint returns table metadata, normalized staged
  row payloads, table-scoped issues, and catalog context.
- `Back to Batch` recovers the batch overview route.

## 2026-05-27 Rates Acceptance Checklist

### Automated Validation

Commands:

```powershell
pytest tests/test_rates_batches.py -q
pytest tests/test_rates_summary.py -q
pytest tests/test_rates_csv_export_artifacts.py tests/test_rates_batch_approval.py -q
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
tests/test_rates_batches.py: 8 passed
tests/test_rates_summary.py: 2 passed
tests/test_rates_csv_export_artifacts.py + tests/test_rates_batch_approval.py: 21 passed
AppFunctionalRates.test.tsx: 4 passed
frontend build: passed
```

Notes:

- A first combined backend command timed out. The same backend files passed
  when split into smaller focused commands.
- The full checklist is recorded in
  `docs/agent/RATES_ACCEPTANCE_CHECKLIST_2026-05-27.md`.

Acceptance result:

- Rates is accepted for the current delivery cycle.
- Remaining items are backlog: backend search operators/pagination, row
  mutation/detail depth, Data Dictionary metadata summary in table detail, and
  expanded out-of-order browser QA.

## 2026-05-28 Context Segregation Foundation Closure

Scope:

- Revalidated the context segregation foundation before closing GitHub issue
  #184.
- No source implementation changed in this closure slice.

Commands:

```powershell
python -m pytest tests/test_operational_scope.py -q
python -m pytest tests/test_modules_navigation.py -q
python -m pytest tests/test_operational_context.py -vv -s
python -m pytest tests/test_operational_metadata.py -q
```

Results:

```text
tests/test_operational_scope.py: 6 passed
tests/test_modules_navigation.py: 10 passed
tests/test_operational_context.py: 26 passed
tests/test_operational_metadata.py: 23 passed
```

Notes:

- A first broad combined pytest command timed out on Windows without returning
  useful evidence. The same representative validation set passed when split.
- GitHub issue #184 was closed after the evidence comment was posted.

## 2026-05-28 Settings Functional QA Sync

Scope:

- Updated `frontend/src/app/AppFunctionalAdmin.test.tsx` so the functional QA
  follows the current Settings surface instead of the older Admin Console /
  Jobs route expectation.
- No product source behavior changed.

Commands:

```powershell
npm run qa:functional:admin
npm test -- src/app/App.test.tsx -t "Settings"
python -m pytest tests/test_operational_context.py -q
npm run build
git diff --check -- frontend/src/app/AppFunctionalAdmin.test.tsx
```

Results:

```text
qa:functional:admin: 1 passed
App.test.tsx - Settings: 2 passed
tests/test_operational_context.py: 26 passed
frontend build: passed with existing Vite large chunk warning
git diff --check: no errors
```

Notes:

- `npm run qa:functional:admin` failed before the update because it still
  expected `Admin Console` heading and Jobs/Audit acceptance behavior. The
  corrected test now validates Settings scope authority, role/user/grant
  authoring, access-policy binding, and return-to-Cockpit recovery link.

## 2026-05-28 Cockpit GitHub Closure

Scope:

- Revalidated Project Cockpit v3 for GitHub issue #186.
- No product source behavior changed in this closure slice.

Commands:

```powershell
python -m pytest tests/test_project_cockpit_summary.py tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "Cockpit"
npm test -- src/app/AppFunctionalShell.test.tsx -t "persists backend-owned context"
```

Results:

```text
tests/test_project_cockpit_summary.py + tests/test_modules_navigation.py: 17 passed
App.test.tsx - Cockpit: 1 passed
AppFunctionalShell.test.tsx - context persistence: 1 passed
```

Existing browser QA evidence:

```text
var/qa/cockpit-public-view.png
var/qa/cockpit-private-scope-viewport.png
var/qa/cockpit-scoped-user.png
var/qa/cockpit-route-recovery.png
```

Notes:

- The accepted Cockpit scope is the v3 single authenticated Cockpit model from
  `AGENTS.md`, `CURRENT_SCOPE.md`, and the v3 wireframe brief.
- The older consolidated Cockpit spec still contains command-center/dashboard
  language and should be cleaned up later so future agents do not revive
  project-management panels.

## 2026-05-28 Workbench Assistant Foundation

Scope:

- Added the Workbench Assistant foundation as a shell overlay and backend API
  package.
- Added assistant migrations, focused tests, frontend shell coverage, browser
  QA automation, and planning/spec documentation.
- Merged through PR #210 with merge commit
  `a7f52d32330a170f97a3e422ecac0e84cbb68f94`.

Commands:

```powershell
python -m alembic upgrade head
python -m pytest tests/test_assistant_source_index.py tests/test_modules_navigation.py -q
npm test -- src/app/AppFunctionalShell.test.tsx -t "Workbench Assistant"
npm run build
node --check scripts/functional-assistant-browser.mjs
npm run qa:functional:assistant:browser
gh pr checks 210 --watch --interval 10
```

Results:

```text
alembic upgrade head: passed against fresh Assistant QA DB
assistant + navigation backend tests: 54 passed
AppFunctionalShell Workbench Assistant test: passed
frontend build: passed with existing Vite large chunk warning
assistant browser QA script syntax: passed
assistant browser QA: passed
PR #210 CI: Backend tests passed, Frontend tests and build passed, CodeRabbit status passed
```

Browser QA freshness evidence:

```text
baseUrl: http://127.0.0.1:5205
apiBaseUrl: http://127.0.0.1:8045
navigationIds:
- master_data
- home
- rates
- load_plan
- assets
- order_release_generator
- integration_mapping
- settings
screenshot: var/qa/workbench-assistant-shell.png
```

Notes:

- The Assistant is intentionally outside the main navigation.
- The assistant source index blocks local `OTM_RESOURCES` as an indexed source
  root while still allowing the SQL helper to use the OTM Data Dictionary.
- In local Windows validation, the OTM Data Dictionary override used
  `OTM_OTM_DATA_DICTIONARY_ROOT` because settings use the `OTM_` env prefix.

## 2026-05-28 Load Plan Route-Level Workflows

Scope:

- Promoted the previously implemented GitHub issue #209 patch to a clean
  branch based on current `main`.
- Adds route-aware Load Plan package operation destinations.
- Adds direct route recovery coverage for
  `/load-plan/packages/package_2/zip-review`.

Commands:

```powershell
npm test -- src/app/AppFunctionalLoadPlan.test.tsx
npm test -- src/app/App.test.tsx -t "Load Plan"
python -m pytest tests/test_load_plan_package_intake.py -q
python -m pytest tests/test_load_plan_cutover_checklist.py -q
python -m pytest tests/test_load_plan_cutover_readiness.py -q
python -m pytest tests/test_load_plan_csvutil_builder.py -q
python -m pytest tests/test_load_plan_zip_analysis.py -q
python -m pytest tests/test_load_plan_sequence_blockers.py -q
python -m pytest tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py -q
python -m pytest tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_readiness_export.py -q
npm run build
```

Results:

```text
AppFunctionalLoadPlan.test.tsx: 2 passed
App.test.tsx - Load Plan: 1 passed, 29 skipped
tests/test_load_plan_package_intake.py: 23 passed
tests/test_load_plan_cutover_checklist.py + tests/test_load_plan_cutover_readiness.py: 22 passed
tests/test_load_plan_csvutil_builder.py + tests/test_load_plan_zip_analysis.py: 28 passed
tests/test_load_plan_sequence_blockers.py: 13 passed
tests/test_load_plan_review_queue.py + tests/test_load_plan_review_decisions.py: 16 passed
tests/test_load_plan_cutover_package_export.py + tests/test_load_plan_cutover_go_no_go.py + tests/test_load_plan_cutover_handoff.py + tests/test_load_plan_readiness_export.py: 25 passed
frontend build: passed with existing Vite large chunk warning
git diff --check: no errors
```

Notes:

- Fresh browser screenshots are not accepted until browser QA passes the live
  `/api/v1/platform/navigation` freshness gate.
- Initial backend attempts without `OTM_OTM_DATA_DICTIONARY_ROOT` failed
  because this clean worktree intentionally does not contain protected local
  `OTM_RESOURCES/`; the reruns with the local Data Dictionary override passed.

## 2026-05-28 Load Plan Browser Closeout

Scope:

- Promotes the previously implemented Load Plan browser closeout patch to a
  clean branch based on current `main`.
- Stabilizes the Load Plan browser QA seed path so Rates batches are created
  inside the active project/environment/profile context.
- Adds an idempotent Alembic migration for the
  `load_plan_packages.domain_name` column required by the current model.

Fresh runtime:

```text
Historical source closeout:
- Backend:  http://127.0.0.1:8052
- Frontend: http://127.0.0.1:5222
- Database: var/qa-load-plan-route-closeout.db
- User:     demo@example.test
```

Live navigation IDs checked before browser QA:

```text
master_data, home, rates, load_plan, assets, order_release_generator,
integration_mapping, settings
```

Commands:

```powershell
python -m pytest tests/test_modules_navigation.py -q
python -m alembic upgrade head
node --check scripts/functional-load-plan-browser.mjs
npm run qa:functional:load-plan:browser # historical source closeout
```

Results:

```text
tests/test_modules_navigation.py: 10 passed
alembic heads: single head c5b9d3a1e6f2
alembic upgrade head: passed against fresh var/qa-load-plan-browser-closeout-promote.db
node --check scripts/functional-load-plan-browser.mjs: passed
git diff --check: no errors
Historical source closeout qa:functional:load-plan:browser: passed
```

Evidence:

```text
var/qa/load-plan-route-closeout.png
```

Notes:

- The first browser QA run failed because the script created a Rates batch
  outside the active scoped context; the script now sends project, environment,
  and profile IDs.
- The second browser QA run exposed the missing
  `load_plan_packages.domain_name` migration; the migration is idempotent.
- The third browser QA run exposed an ambiguous `/load-plan` selector after
  Cockpit accelerator links were added; the script now selects the exact Load
  Plan navigation link.
- The promoted migration was rebased to revise `c4a8e2f7b9d1` so Alembic keeps
  a single head after the Assistant migrations.
- Fresh browser QA was not rerun from this clean promotion branch; rely on the
  historical closeout evidence only for the already closed #207 lane.
