# GUI Master Data Data Factory Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first staged Data Factory GUI workflow for selecting a template, validating it, generating/uploading a workbook, validating relationships, mapping, building output, building CSV, and exporting a package.

**Architecture:** Reuse the existing React/Vite Workbench shell and shared module components. The frontend holds only ephemeral route workflow state; backend APIs remain authoritative for validation, batch status, mapping, output, CSV, export, artifacts, and blocked states.

**Tech Stack:** React + TypeScript + Vite, TanStack Query, Vitest + Testing Library, Playwright browser QA, FastAPI backend contracts.

---

## Scope

This plan implements Linear `OTM-114`.

The first story is:

```text
select template -> validate template -> build workbook -> upload synthetic
workbook -> validate relationships -> map canonical records -> build output ->
build CSV -> export package -> leave route -> return with backend-owned
template state visible
```

Out of scope:

```text
- Coordinate Quality GUI
- template authoring
- spreadsheet editor/preview
- Load Plan registration from Data Factory
- direct OTM import
- durable frontend-only batch history
```

## Files

Modify:

```text
frontend/src/platform/api.ts
frontend/src/platform/types/masterData.ts
frontend/src/platform/hooks/masterData.ts
frontend/src/modules/master-data/MasterDataView.tsx
frontend/src/ui/layouts.css
frontend/package.json
docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/gui/GUI_MVP1_PLAN.md
```

Create:

```text
frontend/src/app/AppFunctionalMasterData.test.tsx
frontend/scripts/functional-master-data-browser.mjs
docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md
```

## Task 1: Add Master Data API Client Coverage

**Files:**

```text
Modify: frontend/src/platform/api.ts
Modify: frontend/src/platform/types/masterData.ts
Modify: frontend/src/platform/hooks/masterData.ts
```

- [ ] **Step 1: Add a multipart upload helper**

Add this helper to `frontend/src/platform/api.ts` after `apiPatch`:

```ts
export async function apiUpload<T>(
  path: string,
  formData: FormData,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: headersFor(options),
    body: formData
  });
  return parseResponse<T>(response);
}
```

Do not set a `Content-Type` header for `FormData`; the browser must add the
multipart boundary.

- [ ] **Step 2: Add Master Data workflow types**

Append these types to `frontend/src/platform/types/masterData.ts`:

```ts
export type MasterDataTemplateValidation = {
  template_code: string;
  valid: boolean;
  severity: string;
  issues: Array<{
    code: string;
    message: string;
    severity?: string;
    table_name?: string;
    column_name?: string;
  }>;
  summary: {
    sheet_count: number;
    field_count: number;
    validated_table_count: number;
    validated_column_count: number;
  };
};

export type MasterDataWorkbookArtifact = {
  template_code: string;
  artifact_id: string;
  file_name: string;
  content_type: string;
  sheet_count: number;
  field_count: number;
};

export type MasterDataBatch = {
  batch_id: string;
  template_code: string;
  status: string;
  file_name?: string;
  sheet_count?: number;
  row_count?: number;
  sheets?: Array<{
    sheet_code: string;
    row_count: number;
  }>;
  summary?: Record<string, unknown>;
};

export type MasterDataRelationshipValidation = {
  batch_id: string;
  status: string;
  valid: boolean;
  issues: Array<{
    code: string;
    message: string;
    severity?: string;
    sheet_code?: string;
    row_number?: number;
  }>;
  summary: Record<string, unknown>;
};

export type MasterDataActionResult = {
  batch_id: string;
  status: string;
  summary?: Record<string, unknown>;
  evidence_id?: string;
  artifact_id?: string;
  manifest_id?: string;
  file_name?: string;
  content_type?: string;
};
```

If TypeScript reveals a mismatch with the exact backend payload, align the
types with backend serializers instead of transforming response names in the
view.

- [ ] **Step 3: Add hooks and action helpers**

Update `frontend/src/platform/hooks/masterData.ts` to import `apiPost` and
`apiUpload`, then add:

```ts
export function validateMasterDataTemplate(token: string, templateCode: string) {
  return apiPost<MasterDataTemplateValidation>(
    `/api/v1/modules/master-data/templates/${templateCode}/validate`,
    {},
    { token }
  );
}

export function buildMasterDataWorkbook(token: string, templateCode: string) {
  return apiPost<MasterDataWorkbookArtifact>(
    `/api/v1/modules/master-data/templates/${templateCode}/build-workbook`,
    {},
    { token }
  );
}

export function uploadMasterDataWorkbook(token: string, templateCode: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<MasterDataBatch>(`/api/v1/modules/master-data/templates/${templateCode}/batches`, formData, {
    token
  });
}

export function validateMasterDataRelationships(token: string, batchId: string) {
  return apiPost<MasterDataRelationshipValidation>(
    `/api/v1/modules/master-data/batches/${batchId}/validate-relationships`,
    {},
    { token }
  );
}

export function mapMasterDataBatch(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/map`, {}, { token });
}

export function buildMasterDataOutput(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/build-output`, {}, {
    token
  });
}

export function buildMasterDataCsv(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(`/api/v1/modules/master-data/batches/${batchId}/build-csv`, {}, { token });
}

export function exportMasterDataCsvPackage(token: string, batchId: string) {
  return apiPost<MasterDataActionResult>(
    `/api/v1/modules/master-data/batches/${batchId}/export-csv-package`,
    {},
    { token }
  );
}
```

- [ ] **Step 4: Run a type-oriented smoke test**

Run:

```powershell
cd frontend
npm run test -- App.test.tsx
```

Expected: existing tests pass or fail only because the new workflow test has
not been written yet.

## Task 2: Write The Functional Master Data Test

**Files:**

```text
Create: frontend/src/app/AppFunctionalMasterData.test.tsx
```

- [ ] **Step 1: Add the failing journey test**

Create a test modeled after `AppFunctionalLoadPlan.test.tsx`.

The mock backend must include:

```text
POST /api/v1/platform/session/login
GET  /api/v1/platform/session/me
GET  /api/v1/platform/navigation
GET  /api/v1/platform/user-preferences
GET  /api/v1/platform/active-context
GET  /api/v1/platform/project-cockpit/summary
GET  /api/v1/platform/projects
GET  /api/v1/platform/profiles
GET  /api/v1/platform/environments
GET  /api/v1/modules/master-data/templates
GET  /api/v1/modules/master-data/templates/REGIONS_BASIC
POST /api/v1/modules/master-data/templates/REGIONS_BASIC/validate
POST /api/v1/modules/master-data/templates/REGIONS_BASIC/build-workbook
POST /api/v1/modules/master-data/templates/REGIONS_BASIC/batches
POST /api/v1/modules/master-data/batches/batch_1/validate-relationships
POST /api/v1/modules/master-data/batches/batch_1/map
POST /api/v1/modules/master-data/batches/batch_1/build-output
POST /api/v1/modules/master-data/batches/batch_1/build-csv
POST /api/v1/modules/master-data/batches/batch_1/export-csv-package
```

The test must assert:

```text
- heading "Data Factory" renders
- aria-label "Data Factory workflow" exists
- template list includes REGIONS_BASIC
- clicking "2 Workbook" shows Validate template and Build workbook
- template validation response is rendered as VALID
- workbook artifact filename regions_basic_v1.xlsx is rendered
- clicking "3 Upload" allows uploading a synthetic File
- upload request body is FormData and uses bearer auth
- clicking "4 Validate" renders relationship validation status
- clicking "5 Map" renders mapping status
- clicking "6 Output" runs build output, build CSV, and export package
- export artifact or manifest id is rendered
- user navigates to Project Cockpit and back to Data Factory
- REGIONS_BASIC remains visible from backend-owned template query
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: FAIL because `MasterDataView` does not render the staged workflow or
action buttons yet.

## Task 3: Implement The Staged Data Factory View

**Files:**

```text
Modify: frontend/src/modules/master-data/MasterDataView.tsx
Modify: frontend/src/ui/layouts.css
```

- [ ] **Step 1: Add stages and workflow state**

Add:

```ts
const masterDataWorkflowStages = [
  { id: "templates", title: "Templates", status: "1" },
  { id: "workbook", title: "Workbook", status: "2" },
  { id: "upload", title: "Upload", status: "3" },
  { id: "validate", title: "Validate", status: "4" },
  { id: "map", title: "Map", status: "5" },
  { id: "output", title: "Output", status: "6" }
] as const;

type MasterDataWorkflowStage = (typeof masterDataWorkflowStages)[number]["id"];
```

Inside `MasterDataView`, add state for `activeStage`, workflow result objects,
`selectedUploadFile`, `operationMessage`, `operationError`, and `isMutating`.

- [ ] **Step 2: Add action handlers**

Add handlers for:

```text
handleValidateTemplate
handleBuildWorkbook
handleUploadWorkbook
handleValidateRelationships
handleMapBatch
handleBuildOutput
handleBuildCsv
handleExportCsvPackage
```

Each handler must:

```text
- clear previous operation message/error
- set isMutating true
- call the backend helper
- store the backend response in state
- render a concise success message
- catch and display backend errors through FeedbackMessage
- set isMutating false in finally
```

Use the exact backend statuses from responses. Do not infer validity in the
frontend except for disabling actions that need a local file or batch id.

- [ ] **Step 3: Render the workflow control**

Inside `ModuleWorkspaceLayout`, change title to `Data Factory workflow` and add:

```tsx
<div className="master-data-workflow" aria-label="Data Factory workflow">
  {masterDataWorkflowStages.map((stage) => (
    <button
      aria-pressed={activeStage === stage.id}
      className={
        activeStage === stage.id
          ? "master-data-workflow-step master-data-workflow-step-active"
          : "master-data-workflow-step"
      }
      key={stage.id}
      onClick={() => setActiveStage(stage.id)}
      type="button"
    >
      <span>{stage.status}</span>
      <strong>{stage.title}</strong>
    </button>
  ))}
</div>
```

- [ ] **Step 4: Render one stage at a time**

Use existing shared components:

```text
Templates: ModuleObjectList
Workbook: OperationalPanel + Button + DetailList + BlockerPanel
Upload: OperationalPanel + file input + Button + DetailList
Validate: OperationalPanel + Button + DetailList + BlockerPanel
Map: OperationalPanel + Button + DetailList
Output: OperationalPanel + three Buttons + DetailList
```

Do not put cards inside cards. Keep `SelectedObjectPanel` as the side context
for template and active batch facts.

- [ ] **Step 5: Add scoped CSS**

Append to `frontend/src/ui/layouts.css`:

```css
.master-data-workflow {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.master-data-workflow-step {
  align-items: center;
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  gap: 8px;
  min-height: 44px;
  padding: 8px 10px;
  text-align: left;
}

.master-data-workflow-step span {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.master-data-workflow-step strong {
  font-size: 13px;
}

.master-data-workflow-step-active {
  background: var(--color-accent-soft);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.master-data-action-bar {
  align-items: end;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
}

.master-data-action-bar label {
  color: var(--color-text-muted);
  display: grid;
  font-size: 12px;
  font-weight: 700;
  gap: 6px;
}

@media (max-width: 900px) {
  .master-data-workflow {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .master-data-action-bar,
  .master-data-workflow {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 6: Run the functional test**

Run:

```powershell
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: PASS.

## Task 4: Add Browser QA Script

**Files:**

```text
Create: frontend/scripts/functional-master-data-browser.mjs
Modify: frontend/package.json
```

- [ ] **Step 1: Create the browser script**

Create a script patterned after `functional-load-plan-browser.mjs`.

The script must:

```text
1. Login as demo@example.test / DemoPass123!
2. Set light, comfortable, expanded preferences
3. Open Data Factory
4. Select or default to REGIONS_BASIC
5. Validate template
6. Build workbook
7. Create a synthetic REGIONS_BASIC workbook in memory using ExcelJS or a
   Blob-compatible browser upload path available in Playwright
8. Upload workbook
9. Validate relationships
10. Map batch
11. Build output
12. Build CSV
13. Export package
14. Navigate home and back
15. Confirm REGIONS_BASIC remains visible
16. Fail on console errors or HTTP >= 400
```

If Node-side workbook creation needs a dependency that is not available,
prefer a tiny synthetic `.xlsx` fixture created through the backend workbook
generation response only if it can be uploaded safely. Do not add new npm
dependencies for this slice unless there is no existing way to create the
workbook.

- [ ] **Step 2: Add npm scripts**

Update `frontend/package.json`:

```json
"qa:functional:master-data": "vitest run src/app/AppFunctionalMasterData.test.tsx",
"qa:functional:master-data:browser": "node scripts/functional-master-data-browser.mjs"
```

Also add `src/app/AppFunctionalMasterData.test.tsx` to the aggregate
`qa:functional` script.

- [ ] **Step 3: Run browser QA**

Run:

```powershell
cd frontend
npm run qa:functional:master-data:browser
```

Expected JSON:

```json
{
  "status": "passed",
  "journey": "master-data-template-workbook-upload-output-export-return"
}
```

If batch return-state cannot be recovered because no read endpoint exists,
the script must still assert template return-state and the docs/Linear update
must record the read endpoint gap.

## Task 5: Update Docs And Linear

**Files:**

```text
Create: docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md
Modify: docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md
Modify: docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
Modify: docs/otm-workbench/gui/GUI_MVP1_PLAN.md
```

- [ ] **Step 1: Create the Data Factory GUI doc**

Document:

```text
Primary pattern: staged workflow + object detail
Delivered story: template -> workbook -> upload -> validate -> map -> output/export
Backend contracts used
Out of scope: Coordinate Quality, template authoring, spreadsheet editor, Load
Plan registration, direct OTM import
Validation commands
```

- [ ] **Step 2: Update QA journey matrix**

Change `/master-data` from PARTIAL/TODO to DONE for the first slice after
functional and browser QA pass. Mention any batch return-state caveat if no
batch read endpoint exists.

- [ ] **Step 3: Update roadmap**

Set Master Data / Data Factory to `First functional slice done` and move the
recommended next target to the next module or to the next agreed GUI slice.

- [ ] **Step 4: Update Linear**

Add a comment to `OTM-114` with:

```text
- delivered scope
- commands run
- remaining gaps
- GitHub branch/commit/PR status
```

## Task 6: Final Verification And GitHub

- [ ] **Step 1: Run frontend checks**

Run:

```powershell
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx guiModuleExperienceArchitectureContract.test.ts
npm run lint
npm run build
npm run qa:functional:master-data:browser
```

Expected: all pass.

- [ ] **Step 2: Run backend checks**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py -q
```

Expected: all pass.

- [ ] **Step 3: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected: no errors. CRLF warnings are acceptable in this Windows workspace.

- [ ] **Step 4: Review scoped diff**

Run:

```powershell
git diff -- frontend/src/modules/master-data/MasterDataView.tsx frontend/src/platform/hooks/masterData.ts frontend/src/platform/types/masterData.ts frontend/src/platform/api.ts frontend/src/app/AppFunctionalMasterData.test.tsx frontend/scripts/functional-master-data-browser.mjs frontend/package.json docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md docs/otm-workbench/gui/GUI_MVP1_PLAN.md
```

Expected: diff only contains OTM-114 work and necessary script/doc updates.

- [ ] **Step 5: Use GitHub**

Because the workspace contains unrelated dirty changes, only stage OTM-114
files if the scoped diff is clean:

```powershell
git add docs/superpowers/specs/2026-05-22-gui-master-data-data-factory-workflow-design.md docs/superpowers/plans/2026-05-22-gui-master-data-data-factory-workflow.md frontend/src/platform/api.ts frontend/src/platform/types/masterData.ts frontend/src/platform/hooks/masterData.ts frontend/src/modules/master-data/MasterDataView.tsx frontend/src/ui/layouts.css frontend/src/app/AppFunctionalMasterData.test.tsx frontend/scripts/functional-master-data-browser.mjs frontend/package.json docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md docs/otm-workbench/gui/GUI_MVP1_PLAN.md
git commit -m "gui: add master data staged workflow"
git push -u origin codex/gui-foundation-integration-pr-plan
```

If staging reveals unrelated changes in shared files, stop and report the
conflict instead of committing mixed work.

## Self-Review

Spec coverage:

```text
- Staged workflow covered by Task 3.
- Backend-owned actions covered by Task 1 and Task 3.
- Functional QA covered by Task 2.
- Browser QA covered by Task 4.
- Docs/Linear/GitHub covered by Task 5 and Task 6.
```

Placeholder scan:

```text
No TBD/TODO placeholders remain. Out-of-scope items are explicitly listed.
```

Type consistency:

```text
Type names are consistent across planned hooks, view state, tests, and docs.
Payload names use backend endpoint response names rather than frontend aliases.
```
