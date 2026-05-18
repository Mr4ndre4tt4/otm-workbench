# Load Plan Sequence Blockers Design

## Context

Load Plan can now register approved Rates CSV exports, build internal CSVUTIL
artifacts, analyze package ZIPs, generate review queue items, and record review
decisions. The next backend slice should make the load sequence operational:
given one or more registered packages, the system should explain what tables
will load, what Data Dictionary dependencies are visible, and what blockers must
be resolved before later readiness/cutover work.

This slice does not execute CSVUTIL, upload to OTM, or produce cutover readiness.
It also does not encode guessed OTM functional behavior. Technical dependencies
must come from the local OTM Data Dictionary JSON files under
`OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`. If a technical or
functional OTM question cannot be answered from existing local context or
official Oracle documentation, the system should surface a blocker or the
implementation should ask for clarification instead of guessing.

## Goal

Add backend/API support for deriving a client-safe Load Plan sequence view with
blockers from packages, ZIP Analysis, review queue decisions, and Data
Dictionary foreign keys.

## Scope

Included:

- New persisted `LoadPlanSequenceSnapshot` model for generated sequence views.
- Alembic migration for `load_plan_sequence_snapshots`.
- Sequence service that derives a snapshot for a package.
- `POST /api/v1/modules/load-plan/sequence/snapshots`.
- `GET /api/v1/modules/load-plan/sequence/snapshots`.
- `GET /api/v1/modules/load-plan/sequence/snapshots/{snapshot_id}`.
- `GET /api/v1/modules/load-plan/sequence?package_id=...` for the latest
  generated view.
- Data Dictionary lookup for each package table's `foreignKeys.parentTableName`.
- Blockers from missing package data, ZIP Analysis findings, unresolved review
  items, and package-external Data Dictionary parent dependencies.
- Client-safe evidence, audit log, and domain event for generated snapshots.

Excluded:

- Cutover readiness.
- Cutover export.
- Package approval or status transition.
- CSVUTIL runtime execution.
- OTM upload, external Oracle calls, or live OTM validation.
- UI.
- Cross-package dependency scheduling.

## Snapshot Model

Add `LoadPlanSequenceSnapshot`:

```text
id
project_id
environment_id
profile_id
package_id
status
sequence_json
blockers_json
summary_json
evidence_id
generated_by
generated_at
created_at
updated_at
```

Indexes:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `status`
- `evidence_id`
- `generated_by`
- `generated_at`

Status values:

- `READY_FOR_REVIEW`: no blockers found for this slice.
- `BLOCKED`: one or more blockers found.

`READY_FOR_REVIEW` does not mean ready for cutover. It only means this sequence
snapshot has no blockers inside this slice's limited checks.

## Sequence Derivation

Input:

- One `LoadPlanPackage`.
- Local OTM Data Dictionary root.

Preconditions:

- Package exists.
- Package has `load_sequence_json`.
- Package has source artifact and manifest references.

For each item in `LoadPlanPackage.load_sequence_json`, create a sequence row:

```json
{
  "position": 1,
  "table_name": "ACCESSORIAL_COST",
  "row_count": 1,
  "requirement_level": "OPTIONAL",
  "dictionary_table_found": true,
  "parent_tables": ["ACCESSORIAL_CODE"],
  "missing_parent_tables_in_package": ["ACCESSORIAL_CODE"],
  "zip_analysis": {
    "latest_analysis_id": "...",
    "finding_count": 1,
    "error_count": 1,
    "warning_count": 0
  },
  "review": {
    "pending_count": 0,
    "needs_manual_action_count": 1,
    "rejected_count": 0,
    "excluded_from_cutover_count": 0,
    "confirmed_count": 0
  }
}
```

Data Dictionary behavior:

- Read `<TABLE_NAME>.json` from the configured dictionary root.
- If the table JSON is missing, add blocker `DICTIONARY_TABLE_MISSING`.
- Read `foreignKeys[].parentTableName` and normalize to uppercase.
- Treat parent tables not present in the same package sequence as
  `PACKAGE_PARENT_TABLE_MISSING`.
- Do not infer whether a parent value already exists in a target OTM instance.
  That requires later environment-aware validation or official Oracle-backed
  rules.

## Blockers

Blockers are client-safe objects:

```json
{
  "code": "REVIEW_ITEM_PENDING",
  "severity": "ERROR",
  "table_name": "ACCESSORIAL_COST",
  "source_type": "load_plan_review_item",
  "source_id": "...",
  "message": "A review item still needs a decision before later readiness checks."
}
```

Blocker codes:

- `PACKAGE_NOT_REGISTERED`: package is missing or not in a usable state.
- `PACKAGE_SEQUENCE_EMPTY`: package has no load sequence.
- `PACKAGE_ARTIFACT_MISSING`: package lacks source artifact or manifest
  reference.
- `ZIP_ANALYSIS_MISSING`: no ZIP Analysis exists for the package.
- `ZIP_ANALYSIS_HAS_ERRORS`: latest ZIP Analysis has one or more error
  findings.
- `REVIEW_ITEM_PENDING`: review item has no decision.
- `REVIEW_ITEM_REJECTED`: latest decision is `REJECTED`.
- `REVIEW_ITEM_NEEDS_MANUAL_ACTION`: latest decision is
  `NEEDS_MANUAL_ACTION`.
- `REVIEW_ITEM_EXCLUDED_FROM_CUTOVER`: latest decision is
  `EXCLUDED_FROM_CUTOVER`.
- `DICTIONARY_TABLE_MISSING`: table JSON is not present in local Data
  Dictionary.
- `PACKAGE_PARENT_TABLE_MISSING`: Data Dictionary foreign key parent table is
  not present in this package sequence.

Severity:

- `ERROR` for missing core package data, ZIP errors, pending/rejected/manual
  review decisions, missing dictionary table, and package-external parent
  tables.
- `WARNING` for `EXCLUDED_FROM_CUTOVER`, because it may be intentional, but must
  remain visible before later readiness.

## API Contract

`POST /api/v1/modules/load-plan/sequence/snapshots`

Request:

```json
{
  "package_id": "..."
}
```

Response:

```json
{
  "id": "...",
  "package_id": "...",
  "status": "BLOCKED",
  "sequence": [],
  "blockers": [],
  "summary": {
    "table_count": 1,
    "row_count": 1,
    "blocker_count": 2,
    "error_count": 2,
    "warning_count": 0,
    "next_actions": ["resolve_review_items"]
  },
  "evidence_id": "...",
  "generated_by": "admin@example.com",
  "generated_at": "..."
}
```

`GET /api/v1/modules/load-plan/sequence/snapshots`

- Optional filters: `package_id`, `status`.
- Returns `PageResponse`.

`GET /api/v1/modules/load-plan/sequence/snapshots/{snapshot_id}`

- Returns one serialized snapshot.

`GET /api/v1/modules/load-plan/sequence?package_id=...`

- Returns latest snapshot for the package.
- If no snapshot exists, returns 404 with a message instructing callers to
  generate one first.

## Evidence And Events

Create client-safe evidence:

```text
source_module: load_plan
evidence_type: load_plan_sequence_snapshot
summary_json:
  source_entity_type: load_plan_sequence_snapshot
  source_entity_id
  package_id
  status
  table_count
  row_count
  blocker_count
  error_count
  warning_count
```

Audit:

- `load_plan.sequence.snapshot.generate`

Domain event:

- `load_plan.sequence.snapshot.generated`

Do not copy raw CSV row values, real client names, or decision note text into
evidence, audit metadata, events, or response examples.

## Next Actions

The summary should include deterministic `next_actions`:

- `run_zip_analysis` when no ZIP Analysis exists.
- `generate_review_queue` when ZIP Analysis has findings but no review items
  exist.
- `decide_review_items` when pending review items exist.
- `resolve_manual_actions` when latest decisions include
  `NEEDS_MANUAL_ACTION`.
- `remove_rejected_items_or_rework_package` when latest decisions include
  `REJECTED`.
- `review_exclusions` when latest decisions include
  `EXCLUDED_FROM_CUTOVER`.
- `review_package_dependencies` when Data Dictionary parent tables are missing
  from the package.
- `ready_for_later_readiness` when no blockers exist.

## Errors

- `404`: package or snapshot does not exist.
- `400`: package lacks sequence or required package metadata.

Use the existing FastAPI route style and client-safe messages.

## Data Safety

- Do not use real client names in docs, tests, audit logs, or events.
- Use synthetic identifiers such as `OTM1`, `PUBLIC`, `DEMO`, and synthetic
  notes only.
- Do not store raw CSV row values in snapshot, evidence, audit metadata, or
  domain events.
- Do not copy review decision notes into sequence blockers.
- Use local Data Dictionary JSON for table dependency facts.

## Testing

Add backend tests with synthetic data only:

- `load_plan_sequence_snapshots` table exists after metadata reset.
- Snapshot generation rejects a missing package.
- Snapshot generation rejects a package with empty load sequence.
- Snapshot generation creates a snapshot, evidence, audit log, and domain event.
- Snapshot sequence rows include Data Dictionary parent table names.
- Missing Data Dictionary table creates `DICTIONARY_TABLE_MISSING`.
- Parent tables not present in package create `PACKAGE_PARENT_TABLE_MISSING`.
- Missing ZIP Analysis creates `ZIP_ANALYSIS_MISSING`.
- Pending review items create `REVIEW_ITEM_PENDING`.
- Latest review decisions drive blockers for `REJECTED`,
  `NEEDS_MANUAL_ACTION`, and `EXCLUDED_FROM_CUTOVER`.
- `CONFIRMED` review items do not create review blockers.
- List, detail, filter, and latest-sequence endpoints work.
- Evidence/audit/event payloads do not include raw row values or decision notes.

## Security And Permissions

Use the existing authenticated route dependency for this slice, matching current
Load Plan endpoints. Later hardening can introduce capability checks for
sequence generation because it influences readiness decisions.

## Risks

Sequence snapshots can be mistaken for cutover readiness. Mitigation: use
`READY_FOR_REVIEW`, not `READY_FOR_CUTOVER`, and keep cutover endpoints out of
scope.

Data Dictionary parent tables can be mistaken for required package contents in
all cases. Mitigation: call them package-external technical dependencies, not
proof that the target OTM environment is missing data.

Functional OTM semantics can be overfit from table names. Mitigation: only use
Data Dictionary facts in this slice; consult official Oracle documentation or
ask before turning a functional assumption into behavior.

## Implementation Notes

Prefer a new focused module:

- `src/otm_workbench/modules/load_plan/sequence.py`

Keep route additions in the existing Load Plan router. Reuse JSON parsing
helpers from `load_plan.packages` and review decision helpers from
`load_plan.review_queue` where useful.

The next slice after this should be Cutover Readiness, built on top of sequence
snapshots rather than duplicating blocker logic.
