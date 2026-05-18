# Load Plan Setup Review Queue Design

## Context

Load Plan can now register approved Rates CSV exports, generate internal
CSVUTIL CTL/CL artifacts, and analyze registered package ZIP files. ZIP
Analysis records client-safe findings, counts, manifest metadata, evidence,
audit, and events, but it intentionally does not decide whether a package can
move forward.

The next roadmap slice is Setup Review Queue. Oracle's CSVUtil documentation
states that CSVUtil import/export handles CSV data and that direct import
validation is primarily database-constraint oriented rather than a full
business-context approval. This slice therefore creates a human review queue
for uncertain setup/package conditions instead of treating local analysis as an
automatic approval.

## Goal

Add backend/API support for generating and listing Load Plan review items from
ZIP Analysis findings and package metadata. The queue should make uncertain or
error-prone items visible before later review decisions and cutover readiness.

## Scope

Included:

- New `LoadPlanReviewItem` persistence model.
- Alembic migration for `load_plan_review_items`.
- Service module for review queue generation and serialization.
- `POST /api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis_id}`.
- `GET /api/v1/modules/load-plan/review-queue`.
- `GET /api/v1/modules/load-plan/review-queue/{item_id}`.
- Client-safe review items created from ZIP Analysis findings.
- Idempotent generation from the same ZIP Analysis.
- Audit log action `load_plan.review_queue.generate_from_zip_analysis`.
- Domain event `load_plan.review_queue.generated`.

Excluded:

- Review decisions.
- Changing review item status beyond initial queue generation.
- Approving or rejecting package readiness.
- Cutover readiness, blockers, checklist, or export.
- OTM upload, CSVUTIL execution, or external Oracle calls.
- UI.

## Oracle Documentation Rule

If implementation uncovers uncertainty about CSVUtil behavior, OTM import
semantics, rate setup rules, or whether a finding should be considered
functionally blocking, stop and consult official Oracle documentation or ask
the product owner. Do not encode guessed OTM behavior into review decisions.

For this slice, review item creation is deliberately conservative:

- Local `ERROR` findings become `PENDING_REVIEW` items.
- Local `WARNING` findings become `PENDING_REVIEW` items.
- Local `INFO` findings do not create review items by default.
- No item is automatically confirmed, rejected, or excluded.

## Model Contract

Add `LoadPlanReviewItem`:

```text
id
project_id
environment_id
profile_id
package_id
zip_analysis_id
source_type
source_code
severity
status
category
table_name
file_name
title
description
details_json
created_by
created_at
updated_at
```

Indexes should follow existing Load Plan style:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `zip_analysis_id`
- `source_type`
- `source_code`
- `severity`
- `status`
- `category`
- `table_name`

Initial values:

- `source_type`: `zip_analysis_finding`.
- `status`: `PENDING_REVIEW`.
- `category`: derived from the finding code with a stable local mapping.

Initial categories:

- `STRUCTURE`: malformed CSV or missing ZIP content.
- `DATA_DICTIONARY`: unknown table or column.
- `DATE_FORMAT`: missing required date format directive.
- `SEQUENCE`: table not in load sequence or row count mismatch.
- `PACKAGE`: package-level missing manifest or package metadata issue.

## Queue Generation Contract

The generator accepts a `LoadPlanZipAnalysis`.

Preconditions:

- ZIP Analysis exists.
- ZIP Analysis status is `ANALYZED`.
- ZIP Analysis has a package id.
- ZIP Analysis findings are readable JSON.

Generation behavior:

- Read `findings_json`.
- Select findings where `severity` is `ERROR` or `WARNING`.
- Create one `LoadPlanReviewItem` per selected finding.
- Preserve table name, file name, source code, severity, and client-safe details.
- Generate stable titles/descriptions from known finding codes.
- If the same analysis/source code/table/file already generated an item, return
  the existing item instead of creating a duplicate.
- Create audit/event records once per generation call, including item counts.

Known code mapping:

```text
ZIP_MANIFEST_MISSING -> PACKAGE
ZIP_CSV_MISSING -> STRUCTURE
CSV_TABLE_LINE_MISSING -> STRUCTURE
CSV_HEADER_LINE_MISSING -> STRUCTURE
CSV_TABLE_NOT_IN_LOAD_SEQUENCE -> SEQUENCE
CSV_TABLE_NOT_IN_DATA_DICTIONARY -> DATA_DICTIONARY
CSV_UNKNOWN_COLUMN -> DATA_DICTIONARY
CSV_DATE_ALTER_SESSION_MISSING -> DATE_FORMAT
CSV_ROW_COUNT_MISMATCH -> SEQUENCE
```

Unknown future finding codes should still create `PENDING_REVIEW` items with
category `PACKAGE` and a generic client-safe title. Do not drop unknown codes.

## API Contract

`POST /api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis_id}`

Response:

```json
{
  "analysis_id": "...",
  "package_id": "...",
  "created_count": 2,
  "existing_count": 0,
  "items": [
    {
      "id": "...",
      "package_id": "...",
      "zip_analysis_id": "...",
      "source_type": "zip_analysis_finding",
      "source_code": "CSV_UNKNOWN_COLUMN",
      "severity": "ERROR",
      "status": "PENDING_REVIEW",
      "category": "DATA_DICTIONARY",
      "table_name": "ACCESSORIAL_COST",
      "file_name": "csv/001_ACCESSORIAL_COST.csv",
      "title": "Unknown OTM Data Dictionary column",
      "description": "A CSV column was not found in the local OTM Data Dictionary and needs review before load planning continues.",
      "details": {
        "column_name": "SYNTHETIC_UNKNOWN_COLUMN"
      },
      "created_by": "admin@example.com"
    }
  ]
}
```

`GET /api/v1/modules/load-plan/review-queue`

Returns `PageResponse` ordered by newest first. It may accept optional filters:

- `status`
- `severity`
- `package_id`
- `zip_analysis_id`

Filters are exact-match only in this slice.

`GET /api/v1/modules/load-plan/review-queue/{item_id}`

Returns one review item or 404.

## Errors

- `404`: ZIP Analysis or review item does not exist.
- `400`: ZIP Analysis is not `ANALYZED`, has unreadable findings JSON, or cannot
  be used to generate review queue items.

Use existing FastAPI route style and client-safe messages.

## Data Safety

Review item content must stay client-safe:

- Store finding code, severity, table name, file name, category, counts, and
  known column names.
- Do not store raw CSV row values.
- Do not store real client names in tests, docs, audit metadata, or events.
- Use synthetic examples such as `OTM1`, `PUBLIC`, `DEMO`, and generated IDs.

## Testing

Add backend tests with synthetic data only:

- Review items table exists after metadata reset.
- Generating from a ZIP Analysis with no ERROR/WARNING findings returns zero
  items.
- Generating from an analysis with `CSV_UNKNOWN_COLUMN` creates one
  `PENDING_REVIEW` item with category `DATA_DICTIONARY`.
- Generation is idempotent for the same analysis and finding.
- List endpoint returns generated review items newest first.
- Detail endpoint returns serialized item with parsed `details`.
- Missing analysis returns 404.
- Audit log and domain event are created for generation.
- Raw values such as `OTM1.ACC_COST_001` do not appear in review item payloads,
  audit metadata, or events.

## Security And Permissions

Use the existing authenticated route dependency. This slice does not add a new
capability model yet, matching current Load Plan endpoints.

Future decision endpoints will require stricter authorization because they
change review status and may influence cutover readiness. That is explicitly
outside this slice.

## Risks

Review queue can be mistaken for decisioning. Mitigation: only create
`PENDING_REVIEW` items and do not add decision endpoints in this slice.

Review queue can be mistaken for OTM validation. Mitigation: item descriptions
must say local package analysis found something to review, not that OTM accepted
or rejected data.

Unknown finding codes can appear as ZIP Analysis evolves. Mitigation: create a
generic pending review item instead of silently ignoring them.

## Implementation Notes

Prefer a focused module `src/otm_workbench/modules/load_plan/review_queue.py`.
Reuse `parse_json_object` and `parse_json_list` from `packages.py`.

Do not modify `LoadPlanZipAnalysis` records during queue generation. The review
queue should reference the analysis, not mutate it.

The next slice after this should be Review Decisions:

- `POST /api/v1/modules/load-plan/review-queue/{item_id}/decide`.
- Status transitions to `CONFIRMED`, `REJECTED`, `NEEDS_MANUAL_ACTION`, or
  `EXCLUDED_FROM_CUTOVER`.
- Decision evidence/audit.
