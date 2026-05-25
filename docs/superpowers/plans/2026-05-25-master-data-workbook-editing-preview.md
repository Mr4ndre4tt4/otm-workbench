# Master Data Workbook Editing Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned workbook editing and preview flow for Master Data so users can prepare Location and Item Packaging rows in the GUI before creating a batch.

**Architecture:** The backend remains the source of truth for template sheets, field labels, required flags, relationship rules, validation, and row-to-workbook conversion. The frontend only renders the backend editor contract and sends row drafts back to the API; it does not infer OTM table structure or relationship rules.

**Tech Stack:** FastAPI, SQLAlchemy, openpyxl, pytest, React, TypeScript, TanStack Query, Vitest, Playwright browser QA.

---

## Scope

Linear: `OTM-127`.

This slice is intentionally smaller than a full Excel replacement. It creates a structured row editor for backend-owned templates and scenario packs, validates required fields and relationships before upload, and creates a normal Master Data batch through the same parsing/mapping pipeline used by uploaded XLSX files.

In scope:
- backend editor contract for a published template
- row-draft validation without persistence
- batch creation from JSON row drafts by generating an in-memory workbook and reusing existing parser behavior
- GUI Workbook stage row editor for Location operational and Item Packaging templates
- React and browser QA for positive and negative human flows

Out of scope:
- formula engine
- arbitrary spreadsheet formatting
- direct OTM import
- real client data

## Files

- Create: `src/otm_workbench/modules/master_data/workbook_editor.py`
  - Pure backend helpers for editor contract, row validation, in-memory workbook creation, and batch creation from row drafts.
- Modify: `src/otm_workbench/modules/master_data/routes.py`
  - Add workbook editor endpoints under existing Master Data router.
- Modify: `tests/test_master_data_templates.py`
  - Add backend tests for contract, validation, relationship errors, and JSON-row batch creation.
- Modify: `frontend/src/platform/types/masterData.ts`
  - Add editor contract, validation, and row-draft request/response types.
- Modify: `frontend/src/platform/hooks/masterData.ts`
  - Add API functions/hooks for editor contract, preview validation, and batch creation.
- Modify: `frontend/src/modules/master-data/MasterDataView.tsx`
  - Add staged Workbook editor panel after template validation and before upload.
- Modify: `frontend/src/app/AppFunctionalMasterData.test.tsx`
  - Add React functional coverage for row editing, validation failure/recovery, and batch creation.
- Modify: `frontend/scripts/functional-master-data-browser.mjs`
  - Add browser journey for backend-owned workbook editor rows.
- Modify: `docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md`
  - Document the workbook editor behavior.
- Modify: `docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md`
  - Move OTM-127 browser/React/backend coverage from gap to active coverage once implemented.

## API Contract

Add these endpoints:

```text
GET  /api/v1/modules/master-data/templates/{template_code}/workbook-editor
POST /api/v1/modules/master-data/templates/{template_code}/workbook-editor/validate
POST /api/v1/modules/master-data/templates/{template_code}/workbook-editor/batches
```

Editor response shape:

```json
{
  "template_code": "ITEM_PACKAGING_OPERATIONAL_QA",
  "sheets": [
    {
      "code": "ITEMS",
      "name": "Items",
      "target_table": "ITEM",
      "fields": [
        {
          "field_key": "item_gid",
          "label": "Item GID",
          "data_type": "string",
          "required": true
        }
      ],
      "starter_rows": [
        {
          "row_id": "ITEMS-1",
          "values": {
            "item_gid": ""
          }
        }
      ]
    }
  ],
  "relationship_rules": [
    {
      "rule_key": "packaged_item_item_parent",
      "parent_sheet_code": "ITEMS",
      "parent_field_key": "item_gid",
      "child_sheet_code": "PACKAGED_ITEMS",
      "child_field_key": "package_item_gid",
      "severity": "ERROR"
    }
  ]
}
```

Row-draft request shape:

```json
{
  "file_name": "item_packaging_editor.xlsx",
  "sheets": [
    {
      "sheet_code": "ITEMS",
      "rows": [
        {
          "row_id": "ITEMS-1",
          "values": {
            "item_gid": "SYN.ITEM_WIDGET",
            "item_xid": "ITEM_WIDGET"
          }
        }
      ]
    }
  ]
}
```

Validation response shape:

```json
{
  "template_code": "ITEM_PACKAGING_OPERATIONAL_QA",
  "valid": false,
  "status": "INVALID",
  "issues": [
    {
      "code": "REQUIRED_FIELD_MISSING",
      "message": "Item GID is required.",
      "severity": "ERROR",
      "sheet_code": "ITEMS",
      "row_id": "ITEMS-1",
      "field_key": "item_gid"
    }
  ],
  "summary": {
    "sheet_count": 4,
    "row_count": 4,
    "issue_count": 1
  }
}
```

## Task 1: Backend Editor Contract

**Files:**
- Create: `src/otm_workbench/modules/master_data/workbook_editor.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Test: `tests/test_master_data_templates.py`

- [x] **Step 1: Write failing backend test for editor contract**

Add:

```python
def test_master_data_workbook_editor_contract_uses_backend_template_definition(client, admin_header):
    response = client.get(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD/workbook-editor",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "ITEMS_PACKAGING_STANDARD"
    assert [sheet["code"] for sheet in payload["sheets"]] == ["ITEMS", "PACKAGING", "TI_HI"]
    assert payload["sheets"][0]["fields"][0]["field_key"] == "item_gid"
    assert payload["sheets"][0]["fields"][0]["required"] is True
    assert payload["sheets"][0]["starter_rows"][0]["values"]["item_gid"] == ""
    assert payload["relationship_rules"][0]["parent_sheet_code"] == "ITEMS"
```

- [x] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py::test_master_data_workbook_editor_contract_uses_backend_template_definition -q
```

Expected: `404 Not Found` or route missing.

- [x] **Step 3: Implement editor contract**

Create `build_master_data_workbook_editor_contract(template: MasterDataTemplate) -> dict[str, object]` in `workbook_editor.py`. It must read `template.definition_json` when present and otherwise use `template.sheets_json`.

Add route:

```python
@router.get("/templates/{template_code}/workbook-editor")
def get_master_data_workbook_editor(template_code: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    if template.status != "PUBLISHED":
        raise api_error(409, "MASTER_DATA_TEMPLATE_NOT_PUBLISHED", "Master Data template must be published before workbook editing.")
    return build_master_data_workbook_editor_contract(template)
```

- [x] **Step 4: Run backend test and verify it passes**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py::test_master_data_workbook_editor_contract_uses_backend_template_definition -q
```

Expected: `1 passed`.

## Task 2: Backend Row Validation

**Files:**
- Modify: `src/otm_workbench/modules/master_data/workbook_editor.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Test: `tests/test_master_data_templates.py`

- [x] **Step 1: Write failing tests for required field and relationship validation**

Add:

```python
def test_master_data_workbook_editor_validation_reports_required_fields(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD/workbook-editor/validate",
        headers=admin_header,
        json={
            "file_name": "items_editor.xlsx",
            "sheets": [{"sheet_code": "ITEMS", "rows": [{"row_id": "ITEMS-1", "values": {"item_gid": ""}}]}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["issues"][0]["code"] == "REQUIRED_FIELD_MISSING"
    assert payload["issues"][0]["field_key"] == "item_gid"


def test_master_data_workbook_editor_validation_reports_relationship_orphans(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD/workbook-editor/validate",
        headers=admin_header,
        json={
            "file_name": "items_editor.xlsx",
            "sheets": [
                {"sheet_code": "ITEMS", "rows": [{"row_id": "ITEMS-1", "values": {"item_gid": "SYN.ITEM_1", "item_xid": "ITEM_1"}}]},
                {"sheet_code": "PACKAGING", "rows": [{"row_id": "PACKAGING-1", "values": {"packaged_item_gid": "SYN.PKG_1", "packaged_item_xid": "PKG_1", "item_gid": "SYN.MISSING_ITEM"}}]},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["code"] == "RELATIONSHIP_PARENT_NOT_FOUND" for issue in payload["issues"])
```

- [x] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py::test_master_data_workbook_editor_validation_reports_required_fields tests/test_master_data_templates.py::test_master_data_workbook_editor_validation_reports_relationship_orphans -q
```

Expected: route missing or validation not implemented.

- [x] **Step 3: Implement validation**

In `workbook_editor.py`, add `validate_master_data_workbook_rows(template, payload)`.

Rules:
- unknown sheet code -> `UNKNOWN_SHEET`
- missing required field value -> `REQUIRED_FIELD_MISSING`
- relationship child value without matching parent value -> `RELATIONSHIP_PARENT_NOT_FOUND`
- empty optional rows are ignored only when every value is blank

Add route:

```python
@router.post("/templates/{template_code}/workbook-editor/validate")
def validate_master_data_workbook_editor_rows(template_code: str, payload: dict[str, object], db: Session = Depends(get_db), user: User = Depends(require_user)):
    template = get_published_master_data_template_or_404(db, template_code)
    return validate_master_data_workbook_rows(template, payload)
```

- [x] **Step 4: Run tests and verify they pass**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py::test_master_data_workbook_editor_validation_reports_required_fields tests/test_master_data_templates.py::test_master_data_workbook_editor_validation_reports_relationship_orphans -q
```

Expected: `2 passed`.

## Task 3: Batch Creation From Edited Rows

**Files:**
- Modify: `src/otm_workbench/modules/master_data/workbook_editor.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Test: `tests/test_master_data_templates.py`

- [x] **Step 1: Write failing test for JSON-row batch creation**

Add:

```python
def test_master_data_workbook_editor_creates_batch_from_valid_rows(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD/workbook-editor/batches",
        headers=admin_header,
        json={
            "file_name": "items_editor.xlsx",
            "sheets": [
                {"sheet_code": "ITEMS", "rows": [{"row_id": "ITEMS-1", "values": {"item_gid": "SYN.ITEM_1", "item_xid": "ITEM_1", "item_name": "Synthetic Item"}}]},
                {"sheet_code": "PACKAGING", "rows": [{"row_id": "PACKAGING-1", "values": {"packaged_item_gid": "SYN.PKG_1", "packaged_item_xid": "PKG_1", "item_gid": "SYN.ITEM_1"}}]},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "ITEMS_PACKAGING_STANDARD"
    assert payload["status"] == "PARSED"
    assert payload["file_name"] == "items_editor.xlsx"
    assert payload["row_count"] == 2
```

- [x] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py::test_master_data_workbook_editor_creates_batch_from_valid_rows -q
```

Expected: route missing.

- [x] **Step 3: Implement batch creation**

Implementation should:
- call `validate_master_data_workbook_rows`
- reject invalid drafts with `422 MASTER_DATA_WORKBOOK_EDITOR_INVALID`
- generate an in-memory `.xlsx` using openpyxl with sheet headers in template field-label order
- call existing `parse_master_data_template_workbook`
- return `serialize_master_data_batch`

- [x] **Step 4: Run backend suite subset**

Run:

```powershell
python -m pytest tests/test_master_data_templates.py -q
```

Expected: all Master Data template tests pass.

## Task 4: Frontend Types And Hooks

**Files:**
- Modify: `frontend/src/platform/types/masterData.ts`
- Modify: `frontend/src/platform/hooks/masterData.ts`
- Test: `frontend/src/app/AppFunctionalMasterData.test.tsx`

- [x] **Step 1: Add failing React assertion around editor fetch**

Extend the Master Data test mock so `/workbook-editor` is expected after selecting Workbook stage. Assert `apiCalls` includes:

```typescript
expect(apiCalls).toContain("/api/v1/modules/master-data/templates/REGIONS_BASIC/workbook-editor");
```

- [x] **Step 2: Run React test and verify it fails**

Run:

```powershell
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: missing API call or unhandled mock path.

- [x] **Step 3: Add types and hooks**

Add:

```typescript
export type MasterDataWorkbookEditor = {
  template_code: string;
  sheets: Array<{
    code: string;
    name: string;
    target_table: string;
    fields: Array<{ field_key: string; label: string; data_type: string; required: boolean }>;
    starter_rows: Array<{ row_id: string; values: Record<string, string> }>;
  }>;
  relationship_rules: Array<Record<string, unknown>>;
};
```

Add hooks/functions:

```typescript
export function useMasterDataWorkbookEditor(token: string, templateCode?: string) {
  return useQuery({
    enabled: Boolean(token && templateCode),
    queryKey: ["modules", "master-data", "workbook-editor", templateCode],
    queryFn: () => apiGet<MasterDataWorkbookEditor>(`/api/v1/modules/master-data/templates/${templateCode}/workbook-editor`, { token })
  });
}
```

- [x] **Step 4: Run React test and verify it passes**

Run:

```powershell
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: pass after mocks are aligned.

## Task 5: Workbook Stage UI

**Files:**
- Modify: `frontend/src/modules/master-data/MasterDataView.tsx`
- Modify: `frontend/src/ui/layouts.css`
- Test: `frontend/src/app/AppFunctionalMasterData.test.tsx`

- [ ] **Step 1: Write failing React test for row validation recovery**

Add a test path that:
- opens `/master-data`
- selects `ITEMS_PACKAGING_STANDARD`
- opens Workbook stage
- edits `Item GID` blank
- clicks `Validate edited rows`
- sees `REQUIRED_FIELD_MISSING`
- fixes `Item GID`
- clicks `Create batch from edited rows`
- sees `Workbook editor batch ... created.`

- [ ] **Step 2: Run React test and verify it fails**

Run:

```powershell
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: controls missing.

- [ ] **Step 3: Implement UI**

Render a compact row editor inside the Workbook stage:
- one tab/section per sheet
- one visible starter row per sheet initially
- required fields visibly marked with existing form styling
- action buttons: `Validate edited rows`, `Create batch from edited rows`, `Reset edited rows`
- validation issues render through `BlockerPanel`
- successful batch creation sets the same `uploadedBatch`/`activeBatch` path used by file upload

- [ ] **Step 4: Run React test and lint**

Run:

```powershell
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
```

Expected: tests and lint pass.

## Task 6: Browser QA And Docs

**Files:**
- Modify: `frontend/scripts/functional-master-data-browser.mjs`
- Modify: `docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md`
- Modify: `docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md`

- [ ] **Step 1: Extend browser QA**

Add browser steps after selecting a template and before file upload:
- enter invalid edited row
- validate and see required-field issue
- fix row
- create batch from edited rows
- continue through relationship validation, map, output, CSV, export, Load Plan handoff, checklist readiness, filters, and route return-state

- [ ] **Step 2: Run browser QA**

Run local API and Vite, then:

```powershell
$env:OTM_WORKBENCH_QA_EMAIL='admin@example.com'
$env:OTM_WORKBENCH_QA_PASSWORD='ChangeMe123!'
npm run qa:functional:master-data:browser
```

Expected: browser journey passes and includes workbook editor branch in its JSON journey name.

- [ ] **Step 3: Update docs and Linear**

Docs must state:
- workbook editor is backend-owned
- file upload remains supported
- scenario packs feed the same editor contract
- browser QA covers validation failure/recovery and batch creation

Add Linear comment to `OTM-127` with commit SHA and validation commands.

## Verification Matrix

Run before commit:

```powershell
python -m pytest tests/test_master_data_templates.py -q
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
npm run qa:functional:master-data:browser
git diff --check
```

Expected:
- all pytest tests pass
- React functional Master Data tests pass
- lint passes
- browser QA passes against local FastAPI + Vite
- only expected CRLF warnings from `git diff --check` on Windows

## Self-Review

- Spec coverage: covers backend-owned editor contract, validation, batch creation, React GUI, browser QA, docs, and Linear update.
- Placeholder scan: no unresolved implementation markers.
- Type consistency: route names, type names, and function names are consistent across backend and frontend tasks.
