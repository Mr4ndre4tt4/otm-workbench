# Master Data Dynamic Template Factory Design

**Status:** implementation started
**Date:** 2026-05-22
**Linear:** OTM-116, child of OTM-115
**Scope:** backend template authoring, validation, mapping model, and runtime
compatibility for Master Data / Data Factory.

## Objective

Move Master Data beyond seeded templates by adding a backend-owned dynamic
template factory.

The factory must let the system define templates from N OTM tables, expose
friendly operator fields, and generate import-ready OTM CSV packages without
putting business truth in the frontend.

## Current Baseline

The current backend already supports the first functional slice:

```text
seeded templates -> validate -> workbook -> upload -> relationship validation
-> canonical records -> output records -> OTM CSV files -> ZIP/evidence
```

The baseline is intentionally narrow:

```text
- templates are seeded in code
- template shape is stored as sheets_json and target_tables_json
- each sheet maps to one target table
- each user field maps to one target column
- relationship rules are hardcoded by template code
```

That is enough for OTM-114, but not enough for module completion under
OTM-115.

## Product Story

An admin or implementation lead can create a reusable Master Data template:

```text
1. create draft template
2. choose catalog macro-object or target OTM tables
3. choose exact OTM target columns from the Data Dictionary-backed Catalog
4. define friendly workbook fields and labels
5. map user fields, fixed values, and defaults into one or more OTM fields
6. group multiple OTM tables into operator-friendly workbook sheets
7. define parent/child relationship rules
8. validate the definition
9. publish a version
10. use the published version in the existing workbook/upload/CSV pipeline
```

## Design Decision

Use a richer versioned JSON definition inside `MasterDataTemplate` first, then
normalize into child tables only after the contract stabilizes.

Reasoning:

```text
- the current model already stores template shape as JSON
- existing runtime can be evolved with compatibility adapters
- frontend authoring is not built yet, so the backend schema may still learn
  from OTM table/catalog use cases
- keeping one persisted definition reduces migration blast radius for OTM-116
```

The implementation should add a `definition_json` column if a migration is
available in this branch. If avoiding a migration is safer in the immediate
slice, the service may derive the v2 definition from `sheets_json`, but the
public API should already speak in the v2 contract.

## Template Definition Contract

The backend contract is `master-data-template-definition/v2`.

```json
{
  "schema_version": "master-data-template-definition/v2",
  "template": {
    "code": "LOCATIONS_CUSTOM",
    "name": "Locations Custom",
    "version": 1,
    "status": "DRAFT",
    "catalog_macro_object_code": "LOCATION",
    "data_category": "MASTER_DATA"
  },
  "target_tables": [
    {
      "table_name": "LOCATION",
      "sequence": 10,
      "required": true
    },
    {
      "table_name": "LOCATION_ADDRESS",
      "sequence": 20,
      "required": false
    }
  ],
  "sheets": [
    {
      "code": "LOCATIONS",
      "name": "Locations",
      "sequence": 10,
      "description": "Operator-friendly location entry sheet",
      "field_keys": ["location_gid", "location_name", "city", "country"]
    }
  ],
  "fields": [
    {
      "field_key": "location_gid",
      "label": "Location ID",
      "data_type": "string",
      "required": true,
      "help_text": "Synthetic location identifier",
      "sheet_code": "LOCATIONS"
    }
  ],
  "mappings": [
    {
      "mapping_key": "location_gid_to_location",
      "source_type": "USER_FIELD",
      "source_field_key": "location_gid",
      "target_table": "LOCATION",
      "target_column": "LOCATION_GID",
      "required": true
    },
    {
      "mapping_key": "domain_fixed",
      "source_type": "FIXED_VALUE",
      "fixed_value": "OTM1",
      "target_table": "LOCATION",
      "target_column": "DOMAIN_NAME",
      "required": false
    }
  ],
  "relationship_rules": [
    {
      "rule_key": "location_address_parent",
      "parent_sheet_code": "LOCATIONS",
      "parent_field_key": "location_gid",
      "child_sheet_code": "LOCATION_ADDRESSES",
      "child_field_key": "location_gid",
      "severity": "ERROR"
    }
  ],
  "documentation_refs": [
    {
      "source_type": "DATA_DICTIONARY",
      "scope": "LOCATION.LOCATION_GID",
      "note": "Validated against local OTM Data Dictionary."
    }
  ]
}
```

## Mapping Semantics

Supported mapping source types:

```text
USER_FIELD
  Takes the value from a workbook/operator field.

FIXED_VALUE
  Writes a literal value to the target OTM column.

DEFAULT_VALUE
  Writes a value when the source field is blank or missing.
```

The same `source_field_key` may feed multiple target table/column pairs. That
is required for one operator field populating N CSV fields.

The same target table/column must not receive multiple unconditional mappings.
If two mappings can write the same target field, validation must require an
explicit precedence rule before publish. OTM-116 should start by rejecting that
ambiguous case.

## Backend Endpoints

Add draft/publish authoring endpoints while preserving existing runtime
endpoints:

```text
POST   /api/v1/modules/master-data/templates/drafts
PATCH  /api/v1/modules/master-data/templates/{template_code}/draft
POST   /api/v1/modules/master-data/templates/{template_code}/validate-definition
POST   /api/v1/modules/master-data/templates/{template_code}/publish
POST   /api/v1/modules/master-data/templates/{template_code}/versions
GET    /api/v1/modules/master-data/templates/{template_code}/definition
```

Runtime endpoints continue to operate on published templates:

```text
POST /templates/{template_code}/validate
POST /templates/{template_code}/build-workbook
POST /templates/{template_code}/batches
POST /batches/{batch_id}/validate-relationships
POST /batches/{batch_id}/map
POST /batches/{batch_id}/build-output
POST /batches/{batch_id}/build-csv
POST /batches/{batch_id}/export-csv-package
```

If a runtime call receives a draft template, return a lifecycle error instead
of trying to generate artifacts from an unpublished definition.

## Validation Rules

Definition validation must check:

```text
- template code is stable, uppercase, and unique per active version
- target tables exist in the local Data Dictionary/Catalog
- target columns exist on their target tables
- sheets reference known field keys
- fields reference valid sheet codes
- mappings reference known user fields when source_type is USER_FIELD
- fixed/default mappings include a value
- target table/column pairs are not ambiguously mapped
- target tables used in mappings are listed in target_tables
- relationship rules reference known sheets and fields
- published templates have at least one sheet, one field, and one mapping
- documentation_refs exist for user-confirmed or Oracle-help decisions when a
  behavior cannot be proven from the local Data Dictionary
```

Do not infer Oracle functional behavior when the Data Dictionary does not prove
it. The backend should persist a note that a decision came from Oracle official
documentation or from explicit user confirmation.

## Runtime Changes

Workbook generation should use the v2 definition:

```text
row 1: friendly labels
row 2: stable field keys
row 3: mapping hints or compact target summaries
row 4+: operator data
```

Parsing should continue to trust field keys over labels. Labels can change
between versions, but field keys are the durable mapping surface.

Canonical mapping should build records from mappings rather than from a simple
field `target_column`:

```text
USER_FIELD     -> read parsed row value
FIXED_VALUE    -> write literal
DEFAULT_VALUE  -> write fallback only when blank/missing
```

Output generation should group mapped payloads by target table and preserve
the target table sequence defined in `target_tables`.

CSV generation should keep using `build_otm_csv_preview` so OTM CSV parity
stays centralized:

```text
line 1: table name
line 2: column names
optional date directive before data rows
data rows
```

## Compatibility Adapter

Seeded v1 templates should be adapted to v2 at read/runtime boundaries:

```text
sheets[].fields[].name          -> fields[].field_key
sheets[].fields[].label         -> fields[].label
sheets[].target_table           -> mappings[].target_table
sheets[].fields[].target_column -> mappings[].target_column
```

Hardcoded `MASTER_DATA_RELATIONSHIP_RULES` should be replaced by
`relationship_rules` in the v2 definition. During transition, seeded templates
may have generated v2 rules equivalent to the hardcoded rules.

## Persistence Notes

Preferred model additions:

```text
MasterDataTemplate.definition_json
MasterDataTemplate.source_status or status retains DRAFT/PUBLISHED/RETIRED
MasterDataTemplate.version remains integer
```

Optional later normalization:

```text
master_data_template_versions
master_data_template_fields
master_data_template_mappings
master_data_template_relationship_rules
```

Do not introduce the normalized tables in OTM-116 unless the JSON approach
blocks validation, versioning, or tests.

## API Payload Rules

All create/update payloads must be synthetic/client-safe by default. The API
must not persist uploaded client examples into seed docs, screenshots, or
fixtures.

Responses should expose:

```text
- template metadata
- version
- status
- validation summary
- blocking issues
- warnings
- counts by table/sheet/field/mapping
```

Responses should not expose local artifact paths.

## Testing

Backend tests for OTM-116 should cover:

```text
- create draft template with N tables
- reject invalid table
- reject invalid column
- reject duplicate ambiguous target mapping
- support one user field mapped to two target columns
- support fixed value mapping
- validate relationship rules from definition_json
- publish only a valid definition
- runtime rejects draft templates
- build workbook from dynamic published template
- upload workbook and map dynamic output records
- build CSV package with exact OTM CSV structure
```

OTM-117 and OTM-119 will cover GUI authoring and destructive/out-of-order
human flows.

## Out Of Scope

This issue does not implement:

```text
- the full template authoring UI
- Oracle documentation scraping or remote lookup automation
- direct OTM import
- spreadsheet editing in browser
- advanced formulas or transformation expressions
- conflict precedence beyond rejecting ambiguous target mappings
```

## Implementation Plan

1. Add v2 schema helpers and adapters for existing seeded templates.
2. Add request/response models for draft create/update/validate/publish.
3. Add validation service using Catalog/Data Dictionary helpers.
4. Add lifecycle endpoints.
5. Evolve workbook, parse, relationship, mapping, output, and CSV generation to
   read v2 definitions through one adapter.
6. Add backend tests for positive, negative, and lifecycle cases.
7. Update docs and Linear with validation evidence.

## Implementation Evidence

2026-05-22 first backend slice delivered:

```text
- added MasterDataTemplate.definition_json
- added Alembic migration f7a2c9d4e6b1
- added draft creation endpoint
- added definition read endpoint
- added definition validation endpoint
- added publish endpoint
- added v1 seeded template -> v2 definition adapter
- blocked workbook/batch runtime for draft templates
- updated mapping runtime to support one-to-many USER_FIELD mappings and
  FIXED_VALUE mappings
```

2026-05-22 second backend slice delivered:

```text
- added PATCH /api/v1/modules/master-data/templates/{template_code}/draft
- rejected draft updates after publish
- added relationship validation from v2 relationship_rules
- preserved legacy relationship issue payloads for seeded templates
- added DEFAULT_VALUE runtime regression coverage for blank user fields
```

2026-05-22 third backend slice delivered:

```text
- added POST /api/v1/modules/master-data/templates/{template_code}/versions
- creates a next draft version under a new template code
- preserves v2 mappings when versioning a published template
- updated dynamic CSV generation to order columns by v2 mapping order
- added dynamic template CSV/ZIP artifact parity regression coverage
```

2026-05-22 backend completion hardening delivered:

```text
- definition validation now requires at least one documentation reference
- accepted documentation reference source types are DATA_DICTIONARY,
  ORACLE_OFFICIAL, and USER_CONFIRMED
- publish remains blocked when documentation traceability is missing
```

## MVP Versioning Decision

For MVP0, template versioning creates a new draft `MasterDataTemplate` row under
a new unique `code`, with `version = source.version + 1`.

This is intentionally simpler than a normalized immutable
`master_data_template_versions` table. It preserves backend-owned version
metadata and keeps dynamic authoring unblocked while the UI authoring workflow
is still being designed.

Before calling Master Data module-complete, revisit whether immutable version
history is required for audit/compliance. If yes, normalize versions in a
dedicated follow-up instead of overloading `code`.

Validation commands:

```text
python -m pytest tests\test_master_data_templates.py -q
python -m pytest tests\test_load_plan_package_intake.py -q -k "master_data"
python -m pytest tests\test_database.py -q
python -m compileall -q src
python -m alembic heads
```

Current result:

```text
- Master Data: 27 passed
- Master Data after third slice: 29 passed
- Master Data after documentation hardening: 30 passed
- Load Plan Master Data package intake: 4 passed
- Database metadata tests: 3 passed
- compileall: passed
- Alembic head: f7a2c9d4e6b1
```

## Open Questions

```text
- Should version publishing create immutable copies immediately, or is
  template row versioning enough for MVP0?
- Which Oracle official/help references should be mandatory for the first
  dynamic templates beyond Data Dictionary validation?
- Should `DEFAULT_VALUE` write only when a user field is blank, or should it
  also write when the user field is absent from the sheet?
```

For OTM-116, the conservative assumption is:

```text
- versioned row is enough for MVP0
- Data Dictionary is mandatory; Oracle/user docs are required only for
  functional ambiguity
- DEFAULT_VALUE applies when the source is absent, null, or blank
```

## Self-Review

This design keeps backend ownership, preserves the current working runtime,
adds authoring/versioning without frontend-only state, supports fixed and
one-to-many mappings, keeps OTM CSV parity centralized, and records where
Oracle official documentation or user confirmation is needed.
