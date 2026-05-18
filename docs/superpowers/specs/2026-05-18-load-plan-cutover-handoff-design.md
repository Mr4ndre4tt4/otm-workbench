# Load Plan Cutover Handoff Design

## Context

Load Plan can now generate cutover readiness, export readiness as an internal
artifact, and archive client-safe evidence through Evidence Hub. What is still
missing is a backend gate that says when a Load Plan package is ready to be
handed off to the later cutover execution flow.

This slice does not upload to OTM, run CSVUTIL, or create a real cutover load
package. It records an internal handoff decision and moves only the Load Plan
package status when the prerequisites are satisfied.

No new OTM table dependency is introduced. Existing dependency logic remains in
the Data Dictionary-backed sequence snapshot slice.

## Decision

Implement **Load Plan Cutover Handoff** as a backend-only eligibility and commit
workflow.

Compared options:

- **Eligibility only:** safest, but it does not leave a durable operational
  marker that the package was handed off.
- **Status transition with handoff record:** gives auditability and a clear
  lifecycle step while still avoiding external execution.
- **Real cutover export/upload:** too early because OTM upload and execution
  policy are not in scope yet.

Recommendation: status transition with handoff record.

## Goals

- Add persistence for `LoadPlanCutoverHandoff`.
- Add an eligibility endpoint for a package.
- Add a commit endpoint that creates a handoff record.
- Transition `LoadPlanPackage.status` to `READY_FOR_CUTOVER` only when eligible.
- Create client-safe `Evidence`, `AuditLog`, and `DomainEvent` records.
- Keep raw CSV values, review notes, artifact file paths, and real client names
  out of handoff metadata.

## Non-Goals

- No OTM upload.
- No CSVUTIL execution.
- No source artifact bytes copied or bundled.
- No Evidence Hub archive generation inside this endpoint.
- No UI.
- No override flow in this slice.
- No real client names or real customer data in docs/tests.

## Eligibility Rules

A package is eligible when all are true:

1. `LoadPlanPackage` exists.
2. Latest `LoadPlanCutoverReadiness` for the package exists.
3. Latest readiness status is `READY`.
4. At least one `LoadPlanReadinessExport` exists for that readiness.
5. At least one client-safe `Evidence` row exists with:
   - `source_module = "evidence_hub"`
   - `evidence_type = "evidence_hub_archive"`
   - `summary_json` containing the readiness export evidence id.

The archive check proves the readiness export has been included in a traceable
Evidence Hub package before handoff.

Ineligible responses include client-safe blockers:

```json
[
  {"code": "CUTOVER_READINESS_MISSING", "severity": "ERROR", "message": "Generate cutover readiness first."},
  {"code": "CUTOVER_READINESS_NOT_READY", "severity": "ERROR", "message": "Latest readiness is not READY."},
  {"code": "READINESS_EXPORT_MISSING", "severity": "ERROR", "message": "Export readiness first."},
  {"code": "EVIDENCE_ARCHIVE_MISSING", "severity": "ERROR", "message": "Archive readiness export evidence first."}
]
```

## API

Eligibility:

```text
GET /api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=...
```

Response:

```json
{
  "package_id": "package-id",
  "eligible": true,
  "status": "ELIGIBLE",
  "readiness_id": "readiness-id",
  "readiness_status": "READY",
  "readiness_export_id": "export-id",
  "readiness_export_evidence_id": "evidence-id",
  "archive_evidence_id": "archive-evidence-id",
  "blockers": [],
  "next_actions": ["commit_cutover_handoff"]
}
```

Commit:

```text
POST /api/v1/modules/load-plan/cutover-handoff
```

Request:

```json
{
  "package_id": "package-id"
}
```

Response:

```json
{
  "id": "handoff-id",
  "package_id": "package-id",
  "status": "READY_FOR_CUTOVER",
  "readiness_id": "readiness-id",
  "readiness_export_id": "export-id",
  "archive_evidence_id": "archive-evidence-id",
  "evidence_id": "handoff-evidence-id",
  "committed_by": "admin@example.com",
  "committed_at": "2026-05-18T00:00:00"
}
```

List/detail:

```text
GET /api/v1/modules/load-plan/cutover-handoff
GET /api/v1/modules/load-plan/cutover-handoff/{handoff_id}
```

## Persistence

New table: `load_plan_cutover_handoffs`

Columns:

- `id`
- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `readiness_id`
- `readiness_export_id`
- `archive_evidence_id`
- `status`
- `evidence_id`
- `summary_json`
- `committed_by`
- `committed_at`
- timestamps

Default handoff status:

```text
READY_FOR_CUTOVER
```

## Evidence, Audit, Event

Evidence:

```text
source_module = "load_plan"
evidence_type = "load_plan_cutover_handoff"
client_safe = true
sensitivity_level = "client_safe"
```

Audit:

```text
action = "load_plan.cutover_handoff.commit"
target_type = "load_plan_cutover_handoff"
target_id = handoff.id
```

Domain event:

```text
event_type = "load_plan.cutover_handoff.committed"
aggregate_type = "load_plan_cutover_handoff"
aggregate_id = handoff.id
```

Metadata must include ids and counts only. It must not include raw CSV row
values, review decision notes, artifact file paths, or real client names.

## Idempotency

If a package already has a `READY_FOR_CUTOVER` handoff, `POST` returns the latest
handoff instead of creating duplicates. The package remains
`READY_FOR_CUTOVER`.

## Testing

Add backend tests with synthetic data only:

- table exists after metadata reset.
- eligibility rejects missing package.
- eligibility reports missing readiness.
- eligibility reports not-ready readiness.
- eligibility reports missing readiness export.
- eligibility reports missing Evidence Hub archive.
- commit creates handoff, evidence, audit, event, and package status transition.
- commit is idempotent.
- list/detail/filter routes work.
- metadata does not include raw CSV values, review notes, file paths, or real
  client names.

## Risks

Handoff can be mistaken for OTM execution. Mitigation: use
`READY_FOR_CUTOVER`, not `LOADED` or `EXECUTED`, and keep OTM calls out of scope.

Archive matching by summary text is simple. Mitigation: MVP0 archive evidence
contains serialized evidence index metadata and this slice checks for the
readiness export evidence id only; a later schema can add first-class archive
membership rows.

Package status transition can hide blocker history. Mitigation: handoff stores
readiness/export/archive ids and keeps evidence/audit/event records.

## Next Steps

After this slice, likely next increments are a controlled override flow for
non-ready handoff, or a real cutover package builder once OTM upload policy is
defined.
