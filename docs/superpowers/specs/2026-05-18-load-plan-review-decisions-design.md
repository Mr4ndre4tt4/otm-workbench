# Load Plan Review Decisions Design

## Context

Load Plan now creates `PENDING_REVIEW` items from ZIP Analysis findings. Those
items make uncertain package conditions visible, but they cannot yet be acted
on. The roadmap calls for review decisions after the review queue, before load
sequence/readiness/cutover behavior.

This slice adds auditable decisions for review items. It does not calculate
cutover readiness, does not mark packages ready, and does not encode guessed
OTM functional rules. If a decision requires OTM-specific interpretation that
is not already clear, consult official Oracle documentation or ask the product
owner before turning it into product behavior.

## Goal

Add backend/API support for deciding Load Plan review queue items, preserving a
decision history, client-safe evidence, audit log, and domain event.

## Scope

Included:

- New `LoadPlanReviewDecision` persistence model.
- Alembic migration for `load_plan_review_decisions`.
- Decision service and serialization.
- `POST /api/v1/modules/load-plan/review-queue/{item_id}/decide`.
- Review item status transition to one of the approved terminal statuses.
- Client-safe evidence with `evidence_type="load_plan_review_decision"`.
- Audit log action `load_plan.review_queue.decide`.
- Domain event `load_plan.review_queue.decided`.
- Detail/list serialization exposing latest decision metadata through existing
  review item payloads.

Excluded:

- Cutover readiness.
- Readiness blockers/checklist/export.
- Automatic package approval.
- OTM upload, CSVUTIL execution, or external Oracle calls.
- Changing package status.
- UI.

## Decision Statuses

Allowed decision statuses:

- `CONFIRMED`
- `REJECTED`
- `NEEDS_MANUAL_ACTION`
- `EXCLUDED_FROM_CUTOVER`

Initial review item status remains `PENDING_REVIEW`.

Decision semantics for this slice:

- `CONFIRMED`: reviewer accepts the item as reviewed for later planning.
- `REJECTED`: reviewer rejects the item or the underlying condition.
- `NEEDS_MANUAL_ACTION`: reviewer says manual action is required before later
  readiness.
- `EXCLUDED_FROM_CUTOVER`: reviewer says this item should not be included in a
  later cutover package.

These statuses record reviewer intent only. They do not make OTM claims and do
not produce cutover readiness.

## Model Contract

Add `LoadPlanReviewDecision`:

```text
id
project_id
environment_id
profile_id
package_id
review_item_id
decision_status
decision_note
evidence_id
decided_by
decided_at
created_at
updated_at
```

Indexes:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `review_item_id`
- `decision_status`
- `evidence_id`
- `decided_by`

This model is append-only. If a reviewer re-decides the same item later, create
a new decision row and update the review item status to the latest decision.

## Decision Contract

Preconditions:

- Review item exists.
- Requested `decision_status` is one of the allowed statuses.
- `decision_note` is optional but must be trimmed and client-safe.

Behavior:

- Create `LoadPlanReviewDecision`.
- Update `LoadPlanReviewItem.status` to `decision_status`.
- Create client-safe `Evidence` linked to the decision.
- Create `AuditLog`.
- Create `DomainEvent`.
- Return serialized decision plus updated item.

Idempotency:

- This slice should not deduplicate decisions. Re-deciding an item records a new
  decision row so history remains auditable.
- The review item status always reflects the latest decision row.

Evidence summary:

```text
source_entity_type: load_plan_review_decision
source_entity_id: decision id
review_item_id
package_id
decision_status
decision_note_present
decided_by
decided_at
```

Evidence must not include raw CSV row values. The note is user-entered text; do
not copy it into audit/event payloads. It may be stored in the decision row and
evidence only as a boolean `decision_note_present` for this slice.

## API Contract

`POST /api/v1/modules/load-plan/review-queue/{item_id}/decide`

Request:

```json
{
  "decision_status": "NEEDS_MANUAL_ACTION",
  "decision_note": "Synthetic reviewer note"
}
```

Response:

```json
{
  "id": "...",
  "review_item_id": "...",
  "package_id": "...",
  "decision_status": "NEEDS_MANUAL_ACTION",
  "decision_note": "Synthetic reviewer note",
  "evidence_id": "...",
  "decided_by": "admin@example.com",
  "decided_at": "...",
  "review_item": {
    "id": "...",
    "status": "NEEDS_MANUAL_ACTION",
    "latest_decision_id": "..."
  }
}
```

Existing `GET /api/v1/modules/load-plan/review-queue` and
`GET /api/v1/modules/load-plan/review-queue/{item_id}` should include:

```json
{
  "latest_decision_id": "...",
  "latest_decision_status": "NEEDS_MANUAL_ACTION",
  "latest_decided_at": "..."
}
```

when a decision exists, and `null` values otherwise.

## Errors

- `404`: Review item does not exist.
- `400`: Invalid decision status.

Use existing FastAPI route style and client-safe messages.

## Data Safety

- Do not store raw CSV row values in evidence, audit, events, or response
  examples.
- Do not use real client names in tests, docs, audit metadata, or events.
- Use synthetic identifiers and notes only.
- Do not copy `decision_note` into audit metadata or domain event payload.
- Keep decision note storage in `LoadPlanReviewDecision.decision_note` only.

## Testing

Add backend tests with synthetic data only:

- `load_plan_review_decisions` table exists after metadata reset.
- Deciding a `PENDING_REVIEW` item creates a decision row, updates item status,
  creates evidence, audit log, and domain event.
- Decision response includes updated review item and latest decision metadata.
- Detail/list review queue endpoints expose latest decision fields.
- Invalid decision status returns 400 and does not change item status.
- Missing review item returns 404.
- Re-deciding creates a second decision row and updates item status to the
  latest decision.
- Audit/event payloads do not contain raw row values or decision notes.

## Security And Permissions

Use the existing authenticated route dependency for this slice, matching current
Load Plan endpoints. Later hardening can introduce capability checks for review
decisions because this operation changes status and can influence readiness.

## Risks

Review decisions can be mistaken for cutover readiness. Mitigation: this slice
only updates review item status and creates decision evidence; readiness remains
a later backend module.

Decision statuses can be mistaken for OTM validation. Mitigation: response,
evidence, and events should describe reviewer decisions only, not OTM acceptance
or rejection.

Decision notes can accidentally leak sensitive content. Mitigation: store notes
only in the decision row, avoid copying them into audit/event payloads, and use
synthetic notes in tests.

## Implementation Notes

Prefer adding decision functions to
`src/otm_workbench/modules/load_plan/review_queue.py` rather than creating a
second small module. Keep the boundary as "review queue behavior".

Extend `serialize_review_item` to compute latest decision metadata from the
database when a session is provided, or create a separate serializer helper for
routes. Keep implementation simple and avoid eager cross-module abstractions.

The next slice after this should be Load Sequence / blockers or Cutover
Readiness, depending on which roadmap risk is more important next.
