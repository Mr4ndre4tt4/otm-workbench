# Master Data Direct OTM Import Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first backend-owned direct OTM import guardrail contract for Master Data without performing any real external OTM submission.

**Architecture:** Master Data remains CSV/package-first. The new slice exposes import readiness and a guarded submit endpoint only after CSV export exists, returns backend-owned blockers/capability requirements, writes safe audit evidence for guard checks, and refuses real submission until connection, credential, environment, and capability governance are designed. The GUI may show the guarded state but must not own the decision.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, React, TypeScript, TanStack Query, Vitest, Playwright browser QA.

---

## Scope

Linear: `OTM-128`.

This is not a real OTM submit implementation. It is the safety foundation that
prevents an operator from mistaking an exported Master Data package for a
governed direct-import path.

Official Oracle references checked before this plan:
- Oracle Administration Guide, Inbound Integration: inbound integration supports HTTP POST, REST JSON, and SOAP; REST should be used where possible, while Transmission XML remains needed when REST does not cover a feature. URL: `https://docs.oracle.com/en/cloud/saas/transportation/26b/otmca/inbound-integration.html`
- Oracle Data Management Guide, Introduction to DB.XML: DB.XML can insert/update/delete directly against OTM/GTM database tables and should be used only by privileged people; imports are limited to database constraints and do not run full business-context validation. URL: `https://docs.oracle.com/en/cloud/saas/transportation/26a/otmdm/db-xml.html`
- Oracle Help, Upload an XML/CSV Transmission: UI upload can import CSV utility files and XML transmissions, extension determines processing, CSV upload/import has size limits, and cache behavior can require follow-up operational steps. URL: `https://docs.oracle.com/en/cloud/saas/transportation/26a/otmol/integration/upload_xml_trans.htm`

In scope:
- backend import readiness endpoint for exported Master Data batches
- guarded direct-import endpoint that always refuses in this slice
- backend-owned capability, connection, credential, artifact, and package blockers
- audit log for guard checks without recording secrets or real endpoints
- GUI Output-stage import guard panel after export
- React/browser QA for guarded state, missing export, route return, and stale-state recovery
- documentation and Linear update

Out of scope:
- real HTTP/SOAP/REST calls to OTM
- real credentials, tokens, endpoints, or client data
- DB.XML generation/submission
- production capability assignment
- retry queue or asynchronous external job execution

## Files

- Create: `src/otm_workbench/modules/master_data/otm_import_guard.py`
  - Pure helper for readiness/guard payloads.
- Modify: `src/otm_workbench/modules/master_data/routes.py`
  - Add readiness and guarded submit endpoints.
- Modify: `tests/test_master_data_direct_otm_import_guard.py`
  - Backend tests for missing batch, missing export, exported package readiness, guarded submit, and audit safety.
- Modify: `frontend/src/platform/types/masterData.ts`
  - Add import readiness/guard response type.
- Modify: `frontend/src/platform/hooks/masterData.ts`
  - Add API functions for readiness and guarded submit.
- Modify: `frontend/src/modules/master-data/MasterDataView.tsx`
  - Add Output-stage import guard panel after CSV package export.
- Modify: `frontend/src/app/AppFunctionalMasterData.test.tsx`
  - Add React coverage for guarded import state and selected-template/batch recovery.
- Modify: `frontend/scripts/functional-master-data-browser.mjs`
  - Extend Master Data browser QA to verify direct import guard after export.
- Modify: `docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md`
  - Document the guarded import contract and official-source rationale.
- Modify: `docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md`
  - Add browser/React/backend coverage.
- Modify: `docs/otm-workbench/gui/GUI_MODULE_API_CONTRACT_MATRIX.md`
  - Add guarded import endpoints to Master Data contract.
- Modify: `docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md`
  - Move `OTM-128` from generic gap to delivered guarded foundation once implemented.

## API Contract

```text
GET  /api/v1/modules/master-data/batches/{batch_id}/otm-import-readiness
POST /api/v1/modules/master-data/batches/{batch_id}/submit-otm
```

Readiness response when exported but not governable:

```json
{
  "batch_id": "md_batch_1",
  "status": "GUARDED",
  "ready": false,
  "required_capability": "master_data.submit_otm",
  "recommended_transport": "CSVUTIL_UPLOAD_OR_INTEGRATION",
  "official_source_basis": [
    "Oracle inbound integration supports HTTP POST, REST JSON, and SOAP.",
    "REST should be preferred where possible; Transmission XML remains for gaps.",
    "DB.XML is privileged and bypasses full business-context validation."
  ],
  "blockers": [
    {
      "code": "OTM_CONNECTION_NOT_CONFIGURED",
      "message": "No governed OTM connection profile is configured for this environment."
    },
    {
      "code": "OTM_CREDENTIALS_NOT_CONFIGURED",
      "message": "No governed OTM credential reference is configured for this environment."
    },
    {
      "code": "OTM_SUBMIT_CAPABILITY_DISABLED",
      "message": "Direct Master Data OTM submit capability is not enabled."
    }
  ],
  "artifact": {
    "artifact_id": "artifact_1",
    "file_name": "master_data_batch_md_batch_1.zip",
    "sha256": "client-safe-sha",
    "content_type": "application/zip"
  }
}
```

Submit response in this slice:

```json
{
  "code": "MASTER_DATA_OTM_IMPORT_DISABLED",
  "message": "Direct Master Data OTM import is disabled until governed connection, credential, environment, and capability controls are configured.",
  "details": {
    "batch_id": "md_batch_1",
    "required_capability": "master_data.submit_otm",
    "reason": "No governed OTM connection/capability exists for direct Master Data import.",
    "readiness_status": "GUARDED"
  }
}
```

## Task 1: Backend Readiness Contract

**Files:**
- Create: `src/otm_workbench/modules/master_data/otm_import_guard.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Test: `tests/test_master_data_direct_otm_import_guard.py`

- [x] **Step 1: Write failing tests for readiness**

Add tests that create a Master Data batch through existing helpers, export CSV package, then call readiness:

```python
def test_master_data_otm_import_readiness_requires_existing_batch(client, admin_header):
    response = client.get(
        "/api/v1/modules/master-data/batches/missing-batch/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "MASTER_DATA_BATCH_NOT_FOUND"


def test_master_data_otm_import_readiness_blocks_unexported_batch(client, admin_header):
    batch = create_master_data_parsed_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "BLOCKED"
    assert payload["ready"] is False
    assert any(blocker["code"] == "MASTER_DATA_EXPORT_REQUIRED" for blocker in payload["blockers"])
    assert payload["artifact"] is None


def test_master_data_otm_import_readiness_is_guarded_after_export(client, admin_header):
    batch = create_exported_master_data_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/otm-import-readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "GUARDED"
    assert payload["ready"] is False
    assert payload["required_capability"] == "master_data.submit_otm"
    assert payload["recommended_transport"] == "CSVUTIL_UPLOAD_OR_INTEGRATION"
    assert payload["artifact"]["content_type"] == "application/zip"
    assert {blocker["code"] for blocker in payload["blockers"]} >= {
        "OTM_CONNECTION_NOT_CONFIGURED",
        "OTM_CREDENTIALS_NOT_CONFIGURED",
        "OTM_SUBMIT_CAPABILITY_DISABLED",
    }
```

- [x] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py -q
```

Expected: route/module missing.

- [x] **Step 3: Implement readiness helper**

Create:

```python
REQUIRED_CAPABILITY = "master_data.submit_otm"
RECOMMENDED_TRANSPORT = "CSVUTIL_UPLOAD_OR_INTEGRATION"

OFFICIAL_SOURCE_BASIS = [
    "Oracle inbound integration supports HTTP POST, REST JSON, and SOAP.",
    "REST should be preferred where possible; Transmission XML remains for gaps.",
    "DB.XML is privileged and bypasses full business-context validation.",
]


def build_master_data_otm_import_readiness(db: Session, batch: MasterDataBatch) -> dict[str, object]:
    blockers: list[dict[str, str]] = []
    artifact_payload = None
    exported_artifacts = master_data_batch_artifacts(db, batch.id)
    export_artifact = next(
        (artifact for artifact, _evidence in exported_artifacts if artifact.artifact_type == "master_data_csv_export_zip"),
        None,
    )
    if batch.status != "EXPORTED" or export_artifact is None:
        blockers.append(
            {
                "code": "MASTER_DATA_EXPORT_REQUIRED",
                "message": "Build CSV and export the Master Data package before direct import readiness can be evaluated.",
            }
        )
    else:
        artifact_payload = {
            "artifact_id": export_artifact.id,
            "file_name": export_artifact.file_name,
            "sha256": export_artifact.sha256,
            "content_type": export_artifact.content_type,
        }
        blockers.extend(
            [
                {
                    "code": "OTM_CONNECTION_NOT_CONFIGURED",
                    "message": "No governed OTM connection profile is configured for this environment.",
                },
                {
                    "code": "OTM_CREDENTIALS_NOT_CONFIGURED",
                    "message": "No governed OTM credential reference is configured for this environment.",
                },
                {
                    "code": "OTM_SUBMIT_CAPABILITY_DISABLED",
                    "message": "Direct Master Data OTM submit capability is not enabled.",
                },
            ]
        )
    return {
        "batch_id": batch.id,
        "status": "BLOCKED" if any(blocker["code"] == "MASTER_DATA_EXPORT_REQUIRED" for blocker in blockers) else "GUARDED",
        "ready": False,
        "required_capability": REQUIRED_CAPABILITY,
        "recommended_transport": RECOMMENDED_TRANSPORT,
        "official_source_basis": OFFICIAL_SOURCE_BASIS,
        "blockers": blockers,
        "artifact": artifact_payload,
    }
```

- [x] **Step 4: Add readiness route**

Add:

```python
@router.get("/batches/{batch_id}/otm-import-readiness")
def get_master_data_otm_import_readiness(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_master_data_batch_or_404(db, batch_id)
    return build_master_data_otm_import_readiness(db, batch)
```

- [x] **Step 5: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py -q
```

Expected: readiness tests pass.

## Task 2: Guarded Submit Contract

**Files:**
- Modify: `src/otm_workbench/modules/master_data/otm_import_guard.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Test: `tests/test_master_data_direct_otm_import_guard.py`

- [x] **Step 1: Write failing guarded-submit tests**

Add:

```python
def test_submit_master_data_batch_to_otm_is_guarded_and_does_not_create_job(client, admin_header, db_session):
    batch = create_exported_master_data_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch['batch_id']}/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "MASTER_DATA_OTM_IMPORT_DISABLED"
    assert payload["details"]["required_capability"] == "master_data.submit_otm"
    assert payload["details"]["readiness_status"] == "GUARDED"
    assert db_session.query(Job).filter(Job.source_module == "master_data").count() == 0


def test_submit_master_data_batch_to_otm_rejects_missing_batch(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/batches/missing-batch/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "MASTER_DATA_BATCH_NOT_FOUND"
```

- [x] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py -q
```

Expected: submit route missing.

- [x] **Step 3: Implement submit guard**

Add route:

```python
@router.post("/batches/{batch_id}/submit-otm")
def submit_master_data_batch_to_otm(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_master_data_batch_or_404(db, batch_id)
    readiness = build_master_data_otm_import_readiness(db, batch)
    db.add(
        AuditLog(
            action="master_data.batch.submit_otm.guard",
            actor=user.email,
            target_type="master_data_batch",
            target_id=batch.id,
            metadata_json=json.dumps(
                {
                    "batch_id": batch.id,
                    "readiness_status": readiness["status"],
                    "required_capability": readiness["required_capability"],
                    "blocker_codes": [blocker["code"] for blocker in readiness["blockers"]],
                },
                sort_keys=True,
            ),
        )
    )
    db.commit()
    raise api_error(
        409,
        "MASTER_DATA_OTM_IMPORT_DISABLED",
        "Direct Master Data OTM import is disabled until governed connection, credential, environment, and capability controls are configured.",
        {
            "batch_id": batch.id,
            "required_capability": readiness["required_capability"],
            "reason": "No governed OTM connection/capability exists for direct Master Data import.",
            "readiness_status": readiness["status"],
        },
    )
```

- [x] **Step 4: Run backend tests**

Run:

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py tests/test_master_data_templates.py -q
```

Expected: direct import guard and existing Master Data tests pass.

## Task 3: Frontend Contract And Output Stage UI

**Files:**
- Modify: `frontend/src/platform/types/masterData.ts`
- Modify: `frontend/src/platform/hooks/masterData.ts`
- Modify: `frontend/src/modules/master-data/MasterDataView.tsx`
- Test: `frontend/src/app/AppFunctionalMasterData.test.tsx`

- [x] **Step 1: Write failing React assertions**

Extend the existing Master Data journey after export:

```typescript
expect(apiCalls).toContain("/api/v1/modules/master-data/batches/md_batch_1/otm-import-readiness");
await userEvent.click(screen.getByRole("button", { name: "Verify OTM import guard" }));
expect(screen.getByLabelText("Master Data OTM import guard")).toHaveTextContent("master_data.submit_otm");
expect(screen.getByLabelText("Master Data OTM import guard")).toHaveTextContent("OTM_CONNECTION_NOT_CONFIGURED");
expect(screen.getByLabelText("Master Data OTM import guard")).not.toHaveTextContent("password");
```

- [x] **Step 2: Run React test and verify failure**

Run:

```powershell
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
```

Expected: hook/UI missing.

- [x] **Step 3: Add types and hooks**

Add:

```typescript
export type MasterDataOtmImportReadiness = {
  batch_id: string;
  status: "BLOCKED" | "GUARDED" | "READY";
  ready: boolean;
  required_capability: string;
  recommended_transport: string;
  official_source_basis: string[];
  blockers: Array<{ code: string; message: string }>;
  artifact: null | {
    artifact_id: string;
    file_name: string;
    sha256: string;
    content_type: string;
  };
};
```

Add functions:

```typescript
export function getMasterDataOtmImportReadiness(token: string, batchId: string) {
  return apiGet<MasterDataOtmImportReadiness>(
    `/api/v1/modules/master-data/batches/${batchId}/otm-import-readiness`,
    { token }
  );
}

export function submitMasterDataBatchToOtm(token: string, batchId: string) {
  return apiPost<Record<string, unknown>>(`/api/v1/modules/master-data/batches/${batchId}/submit-otm`, {}, { token });
}
```

- [x] **Step 4: Add Output-stage guard panel**

In the Output stage, after export package state exists, add a compact panel:
- button `Verify OTM import guard`
- button `Attempt guarded OTM import` only calls backend guard and surfaces backend error
- `BlockerPanel` lists blocker codes/messages
- readiness state clears when selected template or active batch changes
- no endpoint URL, username, password, token, or local path is displayed

- [x] **Step 5: Run React test and lint**

Run:

```powershell
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
```

Expected: tests and lint pass.

## Task 4: Browser QA And Docs

**Files:**
- Modify: `frontend/scripts/functional-master-data-browser.mjs`
- Modify: `docs/otm-workbench/gui/GUI_MASTER_DATA_VIEW.md`
- Modify: `docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md`
- Modify: `docs/otm-workbench/gui/GUI_MODULE_API_CONTRACT_MATRIX.md`
- Modify: `docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md`

- [x] **Step 1: Extend browser QA**

After Master Data export:
- click `Verify OTM import guard`
- assert `MASTER_DATA_OTM_IMPORT_DISABLED` is not shown until submit is attempted
- assert `master_data.submit_otm` appears
- assert `OTM_CONNECTION_NOT_CONFIGURED`, `OTM_CREDENTIALS_NOT_CONFIGURED`, and `OTM_SUBMIT_CAPABILITY_DISABLED` appear
- click `Attempt guarded OTM import`
- assert backend error text appears
- switch template and return to ensure stale guard state clears

- [x] **Step 2: Run browser QA**

Run local API and Vite, then:

```powershell
cd frontend
$env:OTM_WORKBENCH_QA_EMAIL='admin@example.com'
$env:OTM_WORKBENCH_QA_PASSWORD='ChangeMe123!'
npm run qa:functional:master-data:browser
```

Expected: browser journey passes and includes guarded OTM import in the journey name.

- [x] **Step 3: Update docs and Linear**

Docs must state:
- direct OTM import is still disabled
- readiness is backend-owned and based on exported package/artifact
- Oracle official-source basis for REST/Transmission/DB.XML risk
- no real credentials/endpoints/client data are used
- next real-submit work requires explicit connection profile, credential vault reference, environment allow-list, capability governance, audit, retry/job design, and Oracle API decision

Add Linear comment to `OTM-128` with commit SHA and validation commands.

## Verification Matrix

Run before commit:

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py tests/test_master_data_templates.py -q
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
npm run qa:functional:master-data:browser
cd ..
git diff --check
```

Expected:
- backend guard tests pass
- existing Master Data tests pass
- React functional Master Data tests pass
- lint passes
- browser QA passes against local FastAPI + Vite
- only expected CRLF warnings from `git diff --check` on Windows

## Self-Review

- Spec coverage: covers direct import guardrails without unsafe external submission.
- Oracle-source coverage: cites official Oracle docs for inbound methods, REST preference, DB.XML risk, and XML/CSV upload behavior.
- Placeholder scan: no TBD/TODO/fill-later instructions.
- Type consistency: `MasterDataOtmImportReadiness`, `master_data.submit_otm`, and endpoint names match across backend/frontend/test tasks.
