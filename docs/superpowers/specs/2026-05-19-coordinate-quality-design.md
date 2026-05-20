# Coordinate Quality Backend Design

## Context

Source material: `C:/Users/Enzo Trabalho/Documents/Validar latlon/SPEC.md`.

The standalone ValidaLatLon project is a robust latitude/longitude validation and
geocoding tool for logistics locations. For OTM Workbench, the reusable part is
the backend engine: coordinate validation, geocoder orchestration, status
classification, cache behavior, and batch execution semantics.

The GUI, executable packaging, Excel I/O, and direct desktop workflow are out of
scope for this integration.

## Recommendation

Implement Coordinate Quality as a backend-first subcapability of
Master Data / Data Factory, focused on OTM `LOCATION` data.

This should not become a standalone app module in MVP0. It belongs near Location
master data because its inputs and outputs are location records, correction
issues, and client-safe evidence that can later feed CSV generation, cutover
review, and Evidence Hub.

## MVP0 Scope

MVP0 should deliver a reusable backend engine and API contracts without requiring
real external geocoder calls in tests.

Included:

- Pure coordinate validation engine.
- Brazil UF bounding-box validation.
- Input record contract compatible with OTM `LOCATION` exports:
  - `location_gid`
  - `location_name`
  - `address_line`
  - `city`
  - `province_code`
  - `postal_code`
  - `country_code3_gid`
  - `lat`
  - `lon`
- Legacy full-address input support as a normalization layer.
- Geocoder provider interface with fake/test provider support.
- Optional HTTP providers for BrasilAPI, ViaCEP, Photon, and local Nominatim.
- Batch persistence for coordinate quality runs.
- Result persistence per location.
- Status summary and issue counts.
- Artifact/evidence export for client-safe QA review.

Excluded from MVP0:

- Tkinter GUI.
- `.exe` packaging.
- Standalone Excel read/write helpers.
- Mandatory Docker/Nominatim setup.
- Direct update to OTM.
- Automatic mutation of Master Data CSV outputs.

## Architecture

Create a focused package under:

```text
src/otm_workbench/modules/master_data/coordinate_quality/
```

Suggested files:

- `schemas.py`: request/response DTOs and normalized record dataclasses.
- `engine.py`: pure validation and status classification.
- `providers.py`: geocoder provider protocol plus fake provider for tests.
- `http_providers.py`: optional HTTP-backed BrasilAPI, ViaCEP, Photon, Nominatim.
- `services.py`: batch orchestration, persistence, summaries, evidence payloads.
- `routes.py`: API endpoints under `/api/v1/modules/master-data/coordinate-quality`.

The engine should not import FastAPI, SQLAlchemy, or concrete HTTP clients.
The service layer owns database access and job/evidence integration.

## Data Model

Add SQLAlchemy models and migrations:

```text
master_data_coordinate_quality_batches
- id
- source_type
- source_batch_id nullable
- status
- geocoder_base_url nullable
- provider_mode
- total_count
- processed_count
- ok_count
- corrected_count
- review_count
- divergent_count
- failed_count
- input_json
- summary_json
- issues_json
- created_at
- updated_at

master_data_coordinate_quality_results
- id
- batch_id
- location_gid
- location_name nullable
- address_json
- country_code3_gid nullable
- province_code nullable
- postal_code nullable
- lat_orig nullable
- lon_orig nullable
- lat_new nullable
- lon_new nullable
- status
- source nullable
- diff_lat nullable
- diff_lon nullable
- orig_valid_uf nullable
- new_valid_uf nullable
- issue_json
- created_at
- updated_at
```

Keep detailed input/output JSON for auditability, but expose stable scalar
columns for filtering and reporting.

## API Contracts

Health:

```text
GET /api/v1/modules/master-data/coordinate-quality/health
```

Preview validation for small payloads:

```text
POST /api/v1/modules/master-data/coordinate-quality/validate
```

Create persisted batch:

```text
POST /api/v1/modules/master-data/coordinate-quality/batches
```

Fetch batch summary:

```text
GET /api/v1/modules/master-data/coordinate-quality/batches/{batch_id}
```

List results:

```text
GET /api/v1/modules/master-data/coordinate-quality/batches/{batch_id}/results
```

Export evidence package:

```text
POST /api/v1/modules/master-data/coordinate-quality/batches/{batch_id}/export
```

## Status Rules

Reuse the standalone meanings, normalized for API contracts:

```text
OK
CORRECTED
REVIEW
DIVERGENT
GEOCODE_FAILED
NULL_FILLED
```

The original Portuguese labels can be preserved in evidence/report payloads if
needed, but API status values should be stable ASCII enums.

Initial rule mapping:

- `OK`: original coordinate is valid for UF and movement is below threshold.
- `CORRECTED`: original coordinate is invalid and new coordinate is valid.
- `REVIEW`: both original and new coordinates are valid but movement exceeds threshold.
- `DIVERGENT`: original and new coordinates are invalid for UF.
- `GEOCODE_FAILED`: no candidate coordinate was found.
- `NULL_FILLED`: original coordinate was null and provider returned a candidate.

Threshold from standalone MVP: `0.5` degree absolute diff.

## Provider Strategy

MVP0 tests should not call public services. Use provider fakes and deterministic
fixtures.

Runtime provider modes:

```text
fake
http_online
http_local
```

Config:

- `coordinate_quality_geocoder_url`
- default: `https://photon.komoot.io`
- local example: `http://localhost:8080`

HTTP provider implementation can use existing `httpx` instead of adding
`requests`, since `httpx` is already a project dependency.

## Reuse From Standalone

Port with adaptation:

- `UF_BBOX`
- `ISO3_TO_2`
- Brazil country detection
- CEP cleanup and UF extraction helpers
- Photon/Nominatim response parsing
- status classification logic
- cache keys and rate-limit semantics

Do not port directly:

- GUI class and callbacks
- Excel parser/writer
- checkpoint files tied to local file paths
- global mutable runtime config where dependency injection is cleaner

## Integration Points

Master Data:

- Later Location template batches can feed coordinate quality input.
- Coordinate results can become validation issues or suggested corrections.
- MVP0 should not mutate Location CSV output automatically.

Jobs:

- Batch execution can become a `Job` once Jobs Processing Engine hardening is ready.
- Until then, API can run synchronously for small payloads and store batch records.

Evidence Hub:

- Export should create an Artifact, Manifest, Evidence, and AuditLog.
- Evidence must be client-safe and use synthetic/test-safe data in tests.

Catalog Core:

- Later validation should confirm that source fields map to OTM `LOCATION`.
- MVP0 can define the contract without blocking on full Catalog integration.

## Test Strategy

Backend-first tests:

- Engine validates UF bounding boxes.
- Engine classifies `OK`, `CORRECTED`, `REVIEW`, `DIVERGENT`, `GEOCODE_FAILED`, `NULL_FILLED`.
- Provider fake returns deterministic coordinates.
- API validates a small payload without network access.
- Batch create persists summary and row-level results.
- Export creates artifact/evidence/manifest with client-safe summary.

No tests should require Docker, public Photon, BrasilAPI, or ViaCEP.

## Roadmap Position

Coordinate Quality should be placed inside the Master Data roadmap, after the
current template/batch/CSV foundation is stable and before heavy UI work.

Recommended order:

1. Finish Master Data MVP0 hardening for template/batch/output/CSV/evidence.
2. Add Location template foundation if it is not already present.
3. Add Coordinate Quality MVP0 engine and persisted batch API.
4. Connect Coordinate Quality outputs to Master Data validation issues.
5. Add optional local Nominatim and asynchronous Jobs integration.

## Open Decision

For MVP0, default to fake provider in tests and allow HTTP provider only by
explicit configuration. This keeps the module deterministic and avoids public
service dependency during CI/local verification.
