# OTM Schema Pack / Contract Catalog Spec

**Status:** first persistence/API slice delivered
**Linear:** `OTM-163`
**Source discovery:** `docs/otm-workbench/discovery/OTM_26A_WSDL_XSD_DISCOVERY.md`

## Objective

Create a shared backend capability to govern OTM WSDL/XSD contract files as
versioned schema packs and expose reusable contract metadata to Workbench
modules.

This capability must not become a module-specific parser hidden inside
Integration Mapping, Order Release, Master Data, or Rates. The first cut should
be small, auditable, read-mostly, and safe to use as shared infrastructure.

## Non-Negotiable Guardrails

```text
- No real client names, payloads, credentials, URLs, or identifiers.
- Data Dictionary remains the source of truth for CSVUTIL tables, columns,
  dependencies, and load order.
- OTM CSV rules do not change because of XSD discovery.
- WSDL/XSD contracts provide official XML roots, paths, cardinality,
  documentation hints, and service operation metadata.
- Any Oracle functional or technical uncertainty must be validated with Oracle
  official documentation or left as an explicit open question.
- Evidence records must be client-safe and avoid storing raw payload content.
```

## First-Cut Product Problem

Current modules already need official OTM contract knowledge:

```text
- Integration Mapping needs official path browsing when samples are partial.
- Order Release Generator needs Release/Transmission path validation.
- Master Data needs user-friendly hints for Location and Item templates.
- Rates needs XML contract companions for RATE_OFFERING, RATE_GEO, and X_LANE.
- Assets needs a governed place to store WSDL/XSD packs.
- Jobs needs traceable ingestion and validation runs.
- Evidence needs client-safe proof that generated artifacts used a known
  schema pack.
```

Without a shared schema-pack layer, each module will eventually create its own
partial interpretation of the same OTM contracts.

## Domain Model

### SchemaPack

Represents a versioned bundle of WSDL/XSD files.

Required fields:

```text
- id
- code
- name
- otm_version
- source_type: LOCAL_FOLDER | ZIP_ARTIFACT | ASSET
- source_path
- asset_id nullable
- status: DRAFT | INDEXING | READY | FAILED | RETIRED
- namespace_count
- root_count
- operation_count
- content_hash
- created_by
- created_at
- updated_at
```

Notes:

```text
- `source_path` must be local/dev-only or point to an Asset record.
- `content_hash` should be calculated over normalized file metadata plus file
  contents where feasible.
- The MVP0 path may support LOCAL_FOLDER first, then ASSET/ZIP later.
```

### SchemaFile

Represents one XSD or WSDL file inside a pack.

Required fields:

```text
- id
- schema_pack_id
- file_name
- relative_path
- file_type: XSD | WSDL | OTHER
- namespace
- import_count
- top_level_element_count
- complex_type_count
- status: PARSED | SKIPPED | FAILED
- parse_error nullable
```

### SchemaRoot

Represents a top-level XML root or service payload root.

Required fields:

```text
- id
- schema_pack_id
- schema_file_id
- root_name
- namespace
- domain_area
- root_type: DOMAIN_ROOT | ENVELOPE | DBXML | SERVICE_MESSAGE | ROWSET | OTHER
- envelope_role: NONE | TRANSMISSION | DBXML | SERVICE
- recommended_modules
- documentation
```

Examples from OTM 26A:

```text
- Transmission
- PlannedShipment
- Release
- Location
- Item
- RATE_OFFERING
- RATE_GEO
- DBObject
- xml2sql
```

### SchemaPath

Represents a flattened, searchable path under a root.

Required fields:

```text
- id
- schema_root_id
- parent_path nullable
- path
- node_name
- data_type nullable
- min_occurs
- max_occurs
- is_required
- is_repeatable
- documentation
- source_file
- sequence_index
```

Path extraction should support:

```text
- named complexType inside the same XSD file;
- named complexType across XSD files in the same schema pack;
- anonymous complexType;
- sequence;
- choice;
- extension;
- bounded recursion protection.
```

Path extraction can defer:

```text
- perfect namespace-aware cross-file type resolution;
- full simpleType inheritance;
- every namespace edge case;
- exhaustive recursion expansion.
```

### ServiceOperation

Represents a WSDL operation that can be searched or linked to roots later.

Required fields:

```text
- id
- schema_pack_id
- schema_file_id
- service_name
- operation_name
- input_message
- output_message
- fault_message nullable
- target_namespace
- related_roots
```

Examples from OTM 26A:

```text
- TransmissionService.execute
- TransmissionService.publish
- CommandService.xmlImport
- CommandService.xmlExport
- OrderReleaseService.processAction
```

### MacroObjectSchemaLink

Links Catalog Core macro objects to official schema roots.

Required fields:

```text
- id
- macro_object_code
- schema_root_id
- relationship_role: SEMANTIC_ROOT | CSV_COMPANION | IMPORT_WRAPPER | SERVICE_ACTION
- confidence: HIGH | MEDIUM | LOW
- notes
```

Examples:

```text
- RATE_OFFERING -> RATE_OFFERING as SEMANTIC_ROOT / HIGH
- RATE_RECORD -> RATE_GEO as SEMANTIC_ROOT / HIGH
- LOCATION -> Location as SEMANTIC_ROOT / HIGH
- ITEM -> Item as SEMANTIC_ROOT / HIGH
- ORDER_RELEASE -> Release as SEMANTIC_ROOT / MEDIUM until Oracle docs validate
  the final output contract.
```

## API Surface

First cut should be read-heavy and internal/admin-facing.

```text
GET  /api/v1/catalog/schema-packs
GET  /api/v1/catalog/schema-packs/{schema_pack_id}
POST /api/v1/catalog/schema-packs
POST /api/v1/catalog/schema-packs/{schema_pack_id}/index
GET  /api/v1/catalog/schema-roots
GET  /api/v1/catalog/schema-roots/{schema_root_id}
GET  /api/v1/catalog/schema-roots/{schema_root_id}/paths
GET  /api/v1/catalog/schema-operations
GET  /api/v1/catalog/macro-objects/{macro_object_code}/schema-links
```

API rules:

```text
- Creation/indexing requires admin/developer capability.
- Read endpoints should support filters by otm_version, root_name,
  domain_area, recommended_module, file_type, and status.
- Path search should support prefix and text query.
- Responses must not include raw file content.
```

## Jobs

Recommended job types:

```text
- SCHEMA_PACK_INDEX [delivered]
- SCHEMA_PACK_VALIDATE
- SCHEMA_PACK_EXTRACT_PATHS
- SCHEMA_PACK_EXTRACT_OPERATIONS
```

Job outputs should include:

```text
- schema_pack_id
- files_seen
- files_parsed
- files_failed
- roots_created
- paths_created
- operations_created
- warnings_count
- evidence_id
```

## Evidence

Evidence should capture:

```text
- pack code/version/hash
- index job id
- counts by file/root/path/operation
- warning categories
- validation status
- generated timestamp
```

Evidence must not capture:

```text
- raw WSDL/XSD content;
- raw sample payloads;
- real customer names;
- real service URLs;
- credentials.
```

## Module Consumption

### Integration Mapping Studio

Use schema roots and paths to let users start from official OTM roots such as:

```text
- Transmission
- PlannedShipment
- Release
```

This supplements uploaded samples. It should not remove sample-driven parsing.

### Master Data Template Factory

Use `Location` and `Item` roots to enrich field labels, help text, grouping, and
future XML validation. CSV output remains Data-Dictionary/table-first.

### Order Release Generator

Use `Release` and `Transmission` roots to validate generated XML structure and
make template-to-path mapping explicit. TransactionCode handling needs Oracle
functional validation before being locked.

### Rates Studio

Use `RATE_OFFERING`, `RATE_GEO`, and `X_LANE` as XML contract companions for
documentation and validation. Do not derive CSV load order from XSD.

### Assets Library

Store schema packs as governed assets and expose version/hash/status.

### Jobs Processing

Run ingestion and validation without blocking the UI thread.

### Evidence Hub

Show client-safe validation evidence linked to the pack, job, module, and
generated artifact.

## Functional Acceptance Criteria

```text
1. A local synthetic/dev OTM 26A folder can be registered as a SchemaPack.
2. Indexing produces SchemaFile, SchemaRoot, SchemaPath, and ServiceOperation
   rows for the high-value roots/services identified in discovery.
3. APIs can list roots and path catalogs without exposing raw file content.
4. Catalog Core can return schema links for RATE_OFFERING, RATE_RECORD,
   LOCATION, ITEM, and future ORDER_RELEASE macro objects.
5. Evidence records show counts, status, warnings, and hash without payloads.
6. Negative tests cover invalid XSD, missing import, unknown root, duplicate
   root, unsupported recursion, and sensitive-content detection.
7. Documentation states that Data Dictionary remains the CSV truth.
```

Status update:

```text
- Sensitive-content detection delivered for obvious blocked patterns such as
  credential-like assignments and explicit real-client markers.
- WSDL `soap:address location` is intentionally ignored by the indexer because
  service endpoint URLs are environment-specific and must not be persisted.
- Sync API and `SCHEMA_PACK_INDEX` job both fail client-safe when blocked
  content is detected.
- Broader negative QA is still open for invalid XSD, missing import, unknown
  root, duplicate root, and deeper namespace-aware resolution.
```

## Local 26A Validation Snapshot

Controlled local validation was run against the provided OTM 26A folders using
a temporary SQLite database. No raw WSDL/XSD content, endpoint URL, local path,
or client data was committed.

```text
XSD 26A folder:
- files_seen: 31
- files_parsed: 31
- files_failed: 0
- roots_created: 150
- paths_created before same-pack complexType resolution: 38821
- paths_created after same-pack complexType resolution: 104551
- operations_created: 0

WSDL 26A GenericNameSpace folder:
- files_seen: 8
- files_parsed: 8
- files_failed: 0
- roots_created: 0
- paths_created: 0
- operations_created: 13
```

Interpretation:

```text
- The MVP parser can ingest the local OTM 26A XSD/WSDL inventory without parse
  failures.
- XSD roots and same-pack path extraction are already useful for browsing and
  module linking.
- WSDL service operation extraction is usable, while endpoint locations must
  remain non-persistent.
- Same-pack named complexType resolution is available with bounded depth/path
  budgets to avoid recursive/path explosion.
- Functional Oracle/Data Dictionary validation is still required before the path
  catalog should be treated as user-facing guidance.
```

## UI Acceptance Criteria Later

The first UI should be operational and staged:

```text
1. Select schema pack.
2. Review roots/services.
3. Search paths for one selected root.
4. Review linked modules/macro objects.
5. Open evidence for last index/validation job.
```

It must not stack every root, path, operation, and evidence panel on one page.

## Open Questions

```text
1. Is OTM 26A the only baseline for MVP0/MVP1, or should multiple OTM versions
   be supported immediately?
2. Should schema packs be global assets only, project assets only, or both?
3. Should Order Release Generator first target Transmission-wrapped Release or
   OrderReleaseService action payloads?
4. Should DBXML MVP0 stop at wrapper validation or include CommandService
   import/export artifact orchestration?
5. Which Oracle official docs should be linked as the canonical functional
   references per root before exposing guidance to users?
```

## Initial Implementation Slices

```text
Slice 1 - Persistence and seed contract:
- migrations/models for SchemaPack, SchemaFile, SchemaRoot, SchemaPath,
  ServiceOperation, MacroObjectSchemaLink.
- repository/service serializers.
- no UI.
Status: delivered in first backend slice.

Slice 2 - Local folder indexer:
- parse WSDL/XSD inventory;
- extract top-level elements and services;
- produce client-safe evidence.
Status: delivered as a minimal local-folder indexer for XSD/WSDL inventory,
top-level roots, same-file path extraction, WSDL operations, and client-safe
index evidence.
The same indexer is also available through Jobs Processing as
`SCHEMA_PACK_INDEX` with `input.schema_pack_id`.

Slice 3 - Path extraction:
- support same-file and same-pack complexType traversal with bounded recursion;
- create high-value path catalog for Transmission, PlannedShipment, Release,
  Location, Item, RATE_OFFERING, RATE_GEO, DBObject, xml2sql.
Status: delivered for same-file and same-pack named/anonymous complexType
traversal with bounded depth/path budget. High-value roots still need functional
review before user-facing guidance.

Slice 4 - Catalog Core API:
- expose read-only endpoints for packs, roots, paths, operations, and macro
  links.

Slice 5 - Module integration:
- Integration Mapping official path picker;
- Order Release XML validation;
- Master Data hints;
- Rates semantic companion docs.
```
