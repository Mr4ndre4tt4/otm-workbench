# Evidence Hub Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend-only Evidence Hub read surface for listing and detailing client-safe evidence across modules.

**Architecture:** Create a focused `otm_workbench.evidence_hub.routes` module that serializes existing `Evidence` rows with linked `Artifact` and `Manifest` summaries. Include the router in `create_app()` and keep all responses metadata-only: no artifact file paths, no downloads, and no full manifest payloads.

**Tech Stack:** Python, FastAPI, SQLAlchemy ORM, existing `PageResponse`, pytest.

---

## File Structure

- Create `src/otm_workbench/evidence_hub/__init__.py`: package marker.
- Create `src/otm_workbench/evidence_hub/routes.py`: serializers, filters, list/detail routes.
- Modify `src/otm_workbench/main.py`: include Evidence Hub router.
- Create `tests/test_evidence_hub_index.py`: route, filters, detail, and safety tests.
- Modify `README.md`: document backend-only Evidence Hub Index and add test file.

No migration is needed because this slice reads existing `Evidence`, `Artifact`, and `Manifest` tables.

---

### Task 1: Router Skeleton And Authentication

**Files:**
- Create: `src/otm_workbench/evidence_hub/__init__.py`
- Create: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `src/otm_workbench/main.py`
- Create: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Write failing authentication and empty list tests**

Create `tests/test_evidence_hub_index.py`:

```python
def test_evidence_hub_list_requires_authentication(client):
    response = client.get("/api/v1/evidence-hub/evidence")

    assert response.status_code == 401


def test_evidence_hub_list_returns_empty_page(client, admin_header):
    response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: route not found or auth/list tests fail because the router does not exist.

- [ ] **Step 3: Add router skeleton**

Create `src/otm_workbench/evidence_hub/__init__.py`:

```python
```

Create `src/otm_workbench/evidence_hub/routes.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import Evidence, User


router = APIRouter(prefix="/api/v1/evidence-hub", tags=["evidence-hub"])


def serialize_evidence_index_item(evidence: Evidence) -> dict[str, object]:
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "source_module": evidence.source_module,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": {},
        "artifact": None,
        "manifest": None,
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
    }


@router.get("/evidence")
def list_evidence(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = db.query(Evidence).filter(Evidence.client_safe.is_(True)).order_by(Evidence.created_at.desc()).all()
    return PageResponse(items=[serialize_evidence_index_item(item) for item in items], total=len(items))
```

Modify `src/otm_workbench/main.py`:

```python
from otm_workbench.evidence_hub.routes import router as evidence_hub_router
```

Then include it after platform routes:

```python
app.include_router(evidence_hub_router)
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub src/otm_workbench/main.py tests/test_evidence_hub_index.py
git commit -m "feat: add evidence hub index route"
```

---

### Task 2: Client-Safe Serialization With Links

**Files:**
- Modify: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Add linked artifact and manifest tests**

Append to `tests/test_evidence_hub_index.py`:

```python
import json
from pathlib import Path


def create_platform_evidence(client, admin_header):
    artifact_dir = Path("var/test-artifacts/evidence-hub")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifact_dir / "demo.txt"
    artifact_file.write_text("OTM1.ACC_COST_001 should not be exposed", encoding="utf-8")
    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_file),
            "file_name": "demo.zip",
            "content_type": "application/zip",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": json.dumps(
                {
                    "schema_version": "rates-csv-export-manifest/v1",
                    "manifest_type": "rates_csv_export",
                    "raw_value": "OTM1.ACC_COST_001",
                },
                sort_keys=True,
            ),
        },
        headers=admin_header,
    )
    assert manifest.status_code == 200
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": json.dumps({"status": "ok", "note_present": True}, sort_keys=True),
            "artifact_id": artifact.json()["id"],
            "manifest_id": manifest.json()["id"],
        },
        headers=admin_header,
    )
    assert evidence.status_code == 200
    return evidence.json()["id"], artifact.json()["id"], manifest.json()["id"]


def test_evidence_hub_detail_returns_linked_summaries_without_sensitive_fields(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(f"/api/v1/evidence-hub/evidence/{evidence_id}", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == evidence_id
    assert payload["summary"] == {"note_present": True, "status": "ok"}
    assert payload["artifact"]["id"] == artifact_id
    assert payload["artifact"]["file_name"] == "demo.zip"
    assert "file_path" not in payload["artifact"]
    assert payload["manifest"]["id"] == manifest_id
    assert payload["manifest"]["manifest_type"] == "rates_csv_export"
    assert payload["manifest"]["schema_version"] == "rates-csv-export-manifest/v1"
    assert "manifest_json" not in payload["manifest"]
    assert "OTM1.ACC_COST_001" not in str(payload)
```

- [ ] **Step 2: Run targeted test to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py::test_evidence_hub_detail_returns_linked_summaries_without_sensitive_fields -q
```

Expected: FAIL because detail route and linked serializers do not exist yet.

- [ ] **Step 3: Implement serializers and detail route**

Replace `src/otm_workbench/evidence_hub/routes.py` with:

```python
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import Artifact, Evidence, Manifest, User


router = APIRouter(prefix="/api/v1/evidence-hub", tags=["evidence-hub"])


def parse_json_object(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def serialize_artifact_summary(artifact: Artifact | None) -> dict[str, object] | None:
    if artifact is None:
        return None
    return {
        "id": artifact.id,
        "source_module": artifact.source_module,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def serialize_manifest_summary(manifest: Manifest | None) -> dict[str, object] | None:
    if manifest is None:
        return None
    manifest_payload = parse_json_object(manifest.manifest_json)
    return {
        "id": manifest.id,
        "source_module": manifest.source_module,
        "status": manifest.status,
        "manifest_type": manifest_payload.get("manifest_type"),
        "schema_version": manifest_payload.get("schema_version"),
        "created_at": manifest.created_at.isoformat() if manifest.created_at else None,
    }


def serialize_evidence_index_item(db: Session, evidence: Evidence) -> dict[str, object]:
    artifact = db.query(Artifact).filter(Artifact.id == evidence.artifact_id).first() if evidence.artifact_id else None
    manifest = db.query(Manifest).filter(Manifest.id == evidence.manifest_id).first() if evidence.manifest_id else None
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "source_module": evidence.source_module,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": parse_json_object(evidence.summary_json),
        "artifact": serialize_artifact_summary(artifact),
        "manifest": serialize_manifest_summary(manifest),
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
    }


@router.get("/evidence")
def list_evidence(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = db.query(Evidence).filter(Evidence.client_safe.is_(True)).order_by(Evidence.created_at.desc()).all()
    return PageResponse(items=[serialize_evidence_index_item(db, item) for item in items], total=len(items))


@router.get("/evidence/{evidence_id}")
def get_evidence_detail(
    evidence_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    return serialize_evidence_index_item(db, evidence)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: all Evidence Hub tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub/routes.py tests/test_evidence_hub_index.py
git commit -m "feat: expose evidence detail summaries"
```

---

### Task 3: Filters And Client-Safe Default

**Files:**
- Modify: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Add filters and client-safe tests**

Append to `tests/test_evidence_hub_index.py`:

```python
from otm_workbench.models import Evidence


def test_evidence_hub_list_filters_by_metadata(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "status": "CREATED",
            "sensitivity_level": "client_safe",
            "artifact_id": artifact_id,
            "manifest_id": manifest_id,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == evidence_id


def test_evidence_hub_list_defaults_to_client_safe_only(client, admin_header, db_session):
    safe_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)
    unsafe = Evidence(
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"unsafe"}',
        artifact_id=artifact_id,
        manifest_id=manifest_id,
        client_safe=False,
        sensitivity_level="internal",
    )
    db_session.add(unsafe)
    db_session.commit()

    default_response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)
    unsafe_response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={"client_safe": "false"},
        headers=admin_header,
    )

    assert default_response.status_code == 200
    assert [item["id"] for item in default_response.json()["items"]] == [safe_id]
    assert unsafe_response.status_code == 200
    assert unsafe_response.json()["items"][0]["id"] == unsafe.id
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py::test_evidence_hub_list_filters_by_metadata tests/test_evidence_hub_index.py::test_evidence_hub_list_defaults_to_client_safe_only -q
```

Expected: FAIL because query filters are not implemented.

- [ ] **Step 3: Implement filters**

Update the `list_evidence` signature and query in `src/otm_workbench/evidence_hub/routes.py`:

```python
@router.get("/evidence")
def list_evidence(
    source_module: str | None = None,
    evidence_type: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    client_safe: bool = True,
    sensitivity_level: str | None = None,
    artifact_id: str | None = None,
    manifest_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(Evidence).filter(Evidence.client_safe.is_(client_safe))
    if source_module:
        query = query.filter(Evidence.source_module == source_module)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)
    if status:
        query = query.filter(Evidence.status == status)
    if project_id:
        query = query.filter(Evidence.project_id == project_id)
    if sensitivity_level:
        query = query.filter(Evidence.sensitivity_level == sensitivity_level)
    if artifact_id:
        query = query.filter(Evidence.artifact_id == artifact_id)
    if manifest_id:
        query = query.filter(Evidence.manifest_id == manifest_id)
    items = query.order_by(Evidence.created_at.desc()).all()
    return PageResponse(items=[serialize_evidence_index_item(db, item) for item in items], total=len(items))
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: all Evidence Hub tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub/routes.py tests/test_evidence_hub_index.py
git commit -m "feat: filter evidence hub index"
```

---

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Load Plan Readiness Export section:

```markdown
The Evidence Hub Index slice adds backend-only list/detail APIs for client-safe
evidence across modules, including linked artifact and manifest summaries. It
does not download artifacts, build archive packages, expose filesystem paths, or
return full manifest payloads.
```

Add `tests/test_evidence_hub_index.py` to the verification command.

- [ ] **Step 2: Run full verification**

Run:

```powershell
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

- All tests pass.
- Alembic is already at head.
- Ruff reports `All checks passed!`.

- [ ] **Step 3: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected:

```text
## codex/evidence-hub-index
?? OTM_RESOURCES/
```

`OTM_RESOURCES/` must remain untracked.

- [ ] **Step 4: Commit docs**

```powershell
git add README.md
git commit -m "docs: document evidence hub index"
```

- [ ] **Step 5: Open and merge PR**

Push:

```powershell
git push -u origin codex/evidence-hub-index
```

Open PR:

```text
Title: Evidence Hub Index
```

Body:

```markdown
## Summary
- Add backend Evidence Hub list/detail APIs for client-safe evidence.
- Include linked artifact and manifest summaries without file paths or full manifest payloads.
- Add filters for source module, evidence type, status, sensitivity, artifact, and manifest.

## Test plan
- `python -m pytest -q`
- `python -m alembic upgrade head`
- `python -m ruff check src tests`
```

Merge with expected head SHA, then sync `main`:

```powershell
git checkout main
git pull --ff-only origin main
git branch -d codex/evidence-hub-index
git status --short --branch
```

Expected: `main` is current and only `OTM_RESOURCES/` is untracked.

---

## Self-Review Checklist

- Spec coverage: list, detail, filters, linked summaries, safety exclusions, README, and verification are covered.
- Placeholder scan: no deferred implementation text is present.
- Type consistency: route prefix `/api/v1/evidence-hub`, model `Evidence`, linked `Artifact`/`Manifest`, and response keys match the design spec.
- Data safety: examples use synthetic `OTM1`; API responses exclude file paths, full manifests, raw artifact contents, and real client names.
