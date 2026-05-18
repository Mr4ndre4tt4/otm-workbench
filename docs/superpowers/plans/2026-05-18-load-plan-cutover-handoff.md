# Load Plan Cutover Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend-only Load Plan cutover handoff gate that marks packages `READY_FOR_CUTOVER` only after readiness, readiness export, and Evidence Hub archive prerequisites are satisfied.

**Architecture:** Add a `LoadPlanCutoverHandoff` model/migration, a focused `modules/load_plan/cutover_handoff.py` service for eligibility and commit behavior, and thin Load Plan routes. The service reads existing readiness/export/archive evidence records, creates client-safe handoff evidence/audit/event records, and performs an idempotent package status transition without OTM execution.

**Tech Stack:** Python, FastAPI, SQLAlchemy ORM, Alembic, pytest.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `LoadPlanCutoverHandoff`.
- Create `migrations/versions/e6b1c9d4a7f2_load_plan_cutover_handoffs.py`.
- Create `src/otm_workbench/modules/load_plan/cutover_handoff.py`.
- Modify `src/otm_workbench/modules/load_plan/routes.py`.
- Create `tests/test_load_plan_cutover_handoff.py`.
- Modify `README.md`.

No OTM upload, CSVUTIL execution, Evidence Hub archive generation, override flow, UI, or real client names are included.

---

### Task 1: Persistence And Eligibility

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/e6b1c9d4a7f2_load_plan_cutover_handoffs.py`
- Create: `src/otm_workbench/modules/load_plan/cutover_handoff.py`
- Create: `tests/test_load_plan_cutover_handoff.py`

- [ ] Add tests for table existence and eligibility blockers:
  - missing package returns 404 through route.
  - package without readiness returns blocker `CUTOVER_READINESS_MISSING`.
  - readiness status other than `READY` returns `CUTOVER_READINESS_NOT_READY`.
  - `READY` readiness without export returns `READINESS_EXPORT_MISSING`.
  - readiness export without Evidence Hub archive returns `EVIDENCE_ARCHIVE_MISSING`.

- [ ] Add `LoadPlanCutoverHandoff` model and Alembic migration with down_revision `d4e9b2c7a6f1`.

- [ ] Implement `cutover_handoff.py`:
  - constants `ELIGIBLE_STATUS = "ELIGIBLE"` and `READY_FOR_CUTOVER_STATUS = "READY_FOR_CUTOVER"`.
  - `serialize_cutover_handoff`.
  - `cutover_handoff_eligibility`.
  - blocker helper.
  - archive evidence lookup by checking `Evidence.summary_json.contains(readiness_export.evidence_id)`.

- [ ] Add routes:
  - `GET /cutover-handoff/eligibility`
  - `GET /cutover-handoff`
  - `GET /cutover-handoff/{handoff_id}`

- [ ] Run:

```powershell
python -m pytest tests/test_load_plan_cutover_handoff.py -q
```

- [ ] Commit:

```powershell
git add src/otm_workbench/models.py migrations/versions/e6b1c9d4a7f2_load_plan_cutover_handoffs.py src/otm_workbench/modules/load_plan/cutover_handoff.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_cutover_handoff.py
git commit -m "feat: evaluate load plan cutover handoff"
```

---

### Task 2: Commit Handoff, Evidence, Audit, Event

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/cutover_handoff.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_cutover_handoff.py`

- [ ] Add tests for:
  - successful commit creates handoff record, evidence, audit, event, and sets package status `READY_FOR_CUTOVER`.
  - commit rejects ineligible packages with 400 and blockers.
  - commit is idempotent and returns the existing latest handoff.
  - list/detail/filter routes work.
  - metadata excludes raw CSV values, review notes, file paths, and real client names.

- [ ] Implement `commit_cutover_handoff`:
  - call eligibility.
  - return existing handoff if latest status is `READY_FOR_CUTOVER`.
  - create handoff evidence/audit/event.
  - set `LoadPlanPackage.status = "READY_FOR_CUTOVER"`.

- [ ] Add `POST /cutover-handoff`.

- [ ] Run:

```powershell
python -m pytest tests/test_load_plan_cutover_handoff.py -q
```

- [ ] Commit:

```powershell
git add src/otm_workbench/modules/load_plan/cutover_handoff.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_cutover_handoff.py
git commit -m "feat: commit load plan cutover handoff"
```

---

### Task 3: README, Full Verification, PR, Merge

**Files:**
- Modify: `README.md`

- [ ] Add README paragraph:

```markdown
The Load Plan Cutover Handoff slice adds a backend-only eligibility and commit
gate that marks packages `READY_FOR_CUTOVER` only after READY readiness,
readiness export, and Evidence Hub archive evidence exist. It records
client-safe evidence, audit, and domain events without executing CSVUTIL,
uploading to OTM, or creating a real cutover package.
```

- [ ] Run:

```powershell
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

- [ ] Push branch, open PR titled `Load Plan Cutover Handoff`, merge with expected head SHA, sync `main`, and leave `OTM_RESOURCES/` untracked.

---

## Self-Review Checklist

- Spec coverage: eligibility, blockers, persistence, commit, idempotency, package status, evidence/audit/event, list/detail, safety tests, README, and verification are covered.
- Placeholder scan: no deferred implementation text is present.
- Type consistency: table/model/route names and statuses match the design spec.
- Data safety: examples use synthetic `OTM1`; metadata avoids raw values, review notes, file paths, and real client names.
