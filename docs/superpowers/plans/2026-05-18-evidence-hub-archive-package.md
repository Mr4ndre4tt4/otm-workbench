# Evidence Hub Archive Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate metadata-only Evidence Hub archive ZIP packages from filtered client-safe evidence.

**Architecture:** Extend the existing Evidence Hub router with a `POST /archive-packages` endpoint. The endpoint queries client-safe evidence using the existing filter dimensions, serializes evidence/artifact/manifest summaries into deterministic JSON files, writes an archive ZIP, and records Artifact, Manifest, Evidence, AuditLog, and DomainEvent rows.

**Tech Stack:** Python, FastAPI, SQLAlchemy ORM, stdlib `zipfile`/`hashlib`/`json`, existing `file_sha256`, pytest.

---

## File Structure

- Modify `src/otm_workbench/evidence_hub/routes.py`: archive request model, query helper, ZIP writer, persistence, route.
- Modify `tests/test_evidence_hub_index.py`: archive package tests.
- Modify `README.md`: document metadata-only Evidence Hub archive package.

No migration is needed.

---

### Task 1: Archive Package Endpoint And ZIP Contract

**Files:**
- Modify: `src/otm_workbench/evidence_hub/routes.py`
- Modify: `tests/test_evidence_hub_index.py`

- [ ] **Step 1: Add archive tests**

Append tests that:

- POST `/api/v1/evidence-hub/archive-packages` with no evidence and expect `400`.
- Create synthetic evidence with `create_platform_evidence`.
- POST `/api/v1/evidence-hub/archive-packages` with `source_module=rates`, `evidence_type=rates_csv_export`, `status=CREATED`, and `sensitivity_level=client_safe`.
- Assert response has `artifact_id`, `manifest_id`, `evidence_id`, `sha256`, `size_bytes`, and counts.
- Open the resulting archive artifact from the database and assert ZIP entries are:
  - `archive_manifest.json`
  - `evidence_index.json`
  - `artifact_index.json`
  - `manifest_index.json`
- Assert JSON payloads do not include `file_path`, `manifest_json`, or raw synthetic file content.
- Assert AuditLog action `evidence_hub.archive_package.create`.
- Assert DomainEvent type `evidence_hub.archive_package.created`.
- Assert the archive artifact can be downloaded through `/api/v1/evidence-hub/artifacts/{artifact_id}/download`.

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: FAIL because archive route does not exist.

- [ ] **Step 3: Implement archive route**

In `src/otm_workbench/evidence_hub/routes.py`:

- Add imports:
  - `hashlib`
  - `zipfile`
  - `BaseModel`
  - `DomainEvent`
  - `utcnow`
  - `get_settings`
- Add `ArchivePackageRequest` with optional filters:
  - `source_module`
  - `evidence_type`
  - `status`
  - `project_id`
  - `sensitivity_level`
- Add helpers:
  - `json_bytes(payload)`
  - `entry_metadata(path, content)`
  - `archive_filters(payload)`
  - `query_archive_evidence(db, payload)`
  - `unique_linked_summaries(items, key)`
- Add route:
  - `POST /archive-packages`
  - reject empty matching evidence with 400.
  - write archive under `get_settings().artifact_root / "evidence_hub" / "archives" / timestamp`.
  - create archive Artifact/Manifest/Evidence/AuditLog/DomainEvent.
  - commit and return archive metadata.

- [ ] **Step 4: Run Evidence Hub tests**

Run:

```powershell
python -m pytest tests/test_evidence_hub_index.py -q
```

Expected: all Evidence Hub tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/otm_workbench/evidence_hub/routes.py tests/test_evidence_hub_index.py
git commit -m "feat: create evidence hub archive packages"
```

---

### Task 2: README, Full Verification, PR, Merge

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Evidence Hub Artifact Download paragraph:

```markdown
The Evidence Hub Archive Package slice generates metadata-only archive ZIPs from
filtered client-safe evidence, recording artifact, manifest, evidence, audit,
and domain event rows. Source artifact bytes are not bundled; individual
artifact download remains controlled by the audited download endpoint.
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

- [ ] **Step 3: Commit docs**

```powershell
git add README.md
git commit -m "docs: document evidence archive packages"
```

- [ ] **Step 4: Open and merge PR**

Push:

```powershell
git push -u origin codex/evidence-hub-archive-package
```

Open PR:

```text
Title: Evidence Hub Archive Package
```

Body:

```markdown
## Summary
- Add metadata-only Evidence Hub archive package generation.
- Persist archive artifact, manifest, evidence, audit log, and domain event records.
- Keep source artifact bytes out of the archive while allowing archive download through the audited artifact endpoint.

## Test plan
- `python -m pytest -q`
- `python -m alembic upgrade head`
- `python -m ruff check src tests`
```

Merge with expected head SHA, then sync `main` and delete the local branch.

---

## Self-Review Checklist

- Spec coverage: filters, ZIP entries, persistence records, downloadability, safety exclusions, README, and verification are covered.
- Placeholder scan: no deferred implementation text is present.
- Type consistency: route prefix `/api/v1/evidence-hub`, artifact type `evidence_hub_archive_zip`, evidence type `evidence_hub_archive`, audit action, and event type match the design spec.
- Data safety: archive excludes source artifact bytes, file paths, full manifests, raw CSV values, review notes, and real client names.
