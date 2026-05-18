# Evidence Hub Artifact Download Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a controlled Evidence Hub artifact download endpoint with hash validation and audit logging.

**Architecture:** Extend the existing Evidence Hub router with a narrow artifact download route. The route resolves an `Artifact`, verifies at least one linked client-safe `Evidence`, recomputes SHA-256 before serving, writes an `AuditLog` on success, and returns `FileResponse` without exposing filesystem paths in JSON responses.

**Tech Stack:** Python, FastAPI `FileResponse`, SQLAlchemy ORM, existing `file_sha256`, pytest.

---

## File Structure

- Modify `src/otm_workbench/evidence_hub/routes.py`: add download helper functions and route.
- Modify `tests/test_evidence_hub_index.py`: add artifact download tests.
- Modify `README.md`: document backend-only download behavior and test coverage.

No migration is needed.

---

### Task 1: Download Route Eligibility And Missing Cases

**Files:**
- Modify: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Add failing missing/eligibility tests**

Append to `tests/test_evidence_hub_index.py`:

```python
from otm_workbench.models import Artifact


def test_evidence_hub_artifact_download_requires_authentication(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(f"/api/v1/evidence-hub/artifacts/{artifact_id}/download")

    assert response.status_code == 401


def test_evidence_hub_artifact_download_rejects_missing_artifact(client, admin_header):
    response = client.get(
        "/api/v1/evidence-hub/artifacts/missing_artifact/download",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_evidence_hub_artifact_download_rejects_artifact_without_client_safe_evidence(
    client,
    admin_header,
    db_session,
):
    artifact_path = Path("var/test-artifacts/evidence-hub/no-safe-evidence.txt")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic internal artifact", encoding="utf-8")
    artifact = Artifact(
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path=str(artifact_path),
        file_name="no-safe-evidence.zip",
        content_type="application/zip",
        sha256="0" * 64,
        size_bytes=artifact_path.stat().st_size,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.commit()

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact.id}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert str(artifact_path) not in str(response.json())
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_requires_authentication tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_missing_artifact tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_artifact_without_client_safe_evidence -q
```

Expected: FAIL because the download route does not exist.

- [ ] **Step 3: Add route skeleton and eligibility helper**

Update imports in `src/otm_workbench/evidence_hub/routes.py`:

```python
from pathlib import Path

from fastapi.responses import FileResponse

from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest, User
from otm_workbench.platform.services import file_sha256
```

Add helpers before the routes:

```python
def client_safe_evidence_for_artifact(db: Session, artifact_id: str) -> Evidence | None:
    return (
        db.query(Evidence)
        .filter(Evidence.artifact_id == artifact_id)
        .filter(Evidence.client_safe.is_(True))
        .order_by(Evidence.created_at.desc())
        .first()
    )


def downloadable_artifact(db: Session, artifact_id: str) -> tuple[Artifact, Evidence]:
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    evidence = client_safe_evidence_for_artifact(db, artifact_id)
    if artifact is None or evidence is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return artifact, evidence
```

Add route at the end of `routes.py`:

```python
@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    artifact, evidence = downloadable_artifact(db, artifact_id)
    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found.")
    return FileResponse(
        path,
        media_type=artifact.content_type,
        filename=artifact.file_name,
        headers={"X-Artifact-SHA256": artifact.sha256},
    )
```

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_requires_authentication tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_missing_artifact tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_artifact_without_client_safe_evidence -q
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub/routes.py tests/test_evidence_hub_index.py
git commit -m "feat: guard evidence artifact download"
```

---

### Task 2: Successful Download, Hash Validation, And Audit

**Files:**
- Modify: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Add download success, missing file, hash mismatch, and audit tests**

Append to `tests/test_evidence_hub_index.py`:

```python
from otm_workbench.models import AuditLog


def test_evidence_hub_artifact_download_returns_file_and_audit(client, admin_header, db_session):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.content == b"OTM1.ACC_COST_001 should not be exposed"
    assert response.headers["content-type"] == "application/zip"
    assert "demo.zip" in response.headers["content-disposition"]
    assert len(response.headers["x-artifact-sha256"]) == 64
    audit = db_session.query(AuditLog).filter_by(action="evidence_hub.artifact.download").one()
    assert audit.target_type == "artifact"
    assert audit.target_id == artifact_id
    assert artifact_id in audit.metadata_json
    assert evidence_id in audit.metadata_json
    assert "demo.txt" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json


def test_evidence_hub_artifact_download_rejects_missing_file_without_path(
    client,
    admin_header,
    db_session,
):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)
    artifact = db_session.query(Artifact).filter_by(id=artifact_id).one()
    artifact_path = Path(artifact.file_path)
    artifact_path.unlink()
    db_session.commit()

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert str(artifact_path) not in str(response.json())


def test_evidence_hub_artifact_download_rejects_hash_mismatch_without_path(
    client,
    admin_header,
    db_session,
):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)
    artifact = db_session.query(Artifact).filter_by(id=artifact_id).one()
    artifact_path = Path(artifact.file_path)
    artifact_path.write_text("changed synthetic artifact", encoding="utf-8")

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert str(artifact_path) not in str(response.json())
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_returns_file_and_audit tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_missing_file_without_path tests/test_evidence_hub_index.py::test_evidence_hub_artifact_download_rejects_hash_mismatch_without_path -q
```

Expected: FAIL because audit and hash validation are not implemented.

- [ ] **Step 3: Implement hash validation and audit**

Update `download_artifact` in `src/otm_workbench/evidence_hub/routes.py`:

```python
@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    artifact, evidence = downloadable_artifact(db, artifact_id)
    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found.")

    actual_sha256, actual_size = file_sha256(str(path))
    if actual_sha256 != artifact.sha256:
        raise HTTPException(status_code=409, detail="Artifact hash mismatch.")

    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="evidence_hub.artifact.download",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "source_module": artifact.source_module,
                    "evidence_id": evidence.id,
                    "sha256": artifact.sha256,
                    "size_bytes": actual_size,
                },
                sort_keys=True,
            ),
        )
    )
    db.commit()
    return FileResponse(
        path,
        media_type=artifact.content_type,
        filename=artifact.file_name,
        headers={"X-Artifact-SHA256": artifact.sha256},
    )
```

- [ ] **Step 4: Run Evidence Hub tests**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: all Evidence Hub tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub/routes.py tests/test_evidence_hub_index.py
git commit -m "feat: audit evidence artifact downloads"
```

---

### Task 3: README, Full Verification, PR, Merge

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Evidence Hub Index paragraph:

```markdown
The Evidence Hub Artifact Download slice adds an authenticated artifact download
endpoint for artifacts linked to client-safe evidence. It recomputes SHA-256
before serving files, audits successful downloads, and does not expose
filesystem paths in API responses.
```

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
## codex/evidence-hub-artifact-download
?? OTM_RESOURCES/
```

`OTM_RESOURCES/` must remain untracked.

- [ ] **Step 4: Commit docs**

```powershell
git add README.md
git commit -m "docs: document evidence artifact download"
```

- [ ] **Step 5: Open and merge PR**

Push:

```powershell
git push -u origin codex/evidence-hub-artifact-download
```

Open PR:

```text
Title: Evidence Hub Artifact Download
```

Body:

```markdown
## Summary
- Add authenticated Evidence Hub artifact download by artifact id.
- Require linked client-safe evidence before serving files.
- Recompute artifact SHA-256 and audit successful downloads without exposing file paths.

## Test plan
- `python -m pytest -q`
- `python -m alembic upgrade head`
- `python -m ruff check src tests`
```

Merge with expected head SHA, then sync `main`:

```powershell
git checkout main
git pull --ff-only origin main
git branch -d codex/evidence-hub-artifact-download
git status --short --branch
```

Expected: `main` is current and only `OTM_RESOURCES/` is untracked.

---

## Self-Review Checklist

- Spec coverage: auth, eligibility, missing artifact, missing file, hash mismatch, successful file response, audit, README, and verification are covered.
- Placeholder scan: no deferred implementation text is present.
- Type consistency: route prefix `/api/v1/evidence-hub`, model names, audit action, and header `X-Artifact-SHA256` match the design spec.
- Data safety: errors and audit metadata avoid file paths, raw file contents, raw CSV values, and real client names.
