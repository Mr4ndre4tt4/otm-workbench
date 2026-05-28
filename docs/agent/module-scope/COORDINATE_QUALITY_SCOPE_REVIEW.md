# Coordinate Quality Scope Review

**Status:** validated for wireframe brief as a Master Data Quality Tools route
family, pending user approval before cleanup or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`
**Supporting spec:** `docs/superpowers/specs/2026-05-19-coordinate-quality-design.md`

## 1. Original Intent

Coordinate Quality validates Location coordinates and exports client-safe review
or correction artifacts. It supports Master Data quality, but it is not part of
the operational Data Factory CSV export path.

## 2. Current Evidence

Master Data redesign delivered Quality Tools routes:

```text
/master-data/quality
/master-data/quality/lat-lon
/master-data/quality/lat-lon/batches/:batchId
```

Completion evidence records persisted coordinate quality batches, result
detail, export, route recovery, and screenshots.

## 3. Validated Target Scope

Coordinate Quality should remain a Quality Tools route family under Master
Data:

- quality tools hub;
- Lat/Lon validator workspace;
- upload/preview of synthetic-safe location data;
- persisted validation batch;
- result detail with issue grouping;
- correction/review package export;
- guarded download/evidence links.

## 4. Explicit Non-Scope

- Do not make Lat/Lon a Data Factory export step.
- Do not make Coordinate Quality a top-level module unless a future scope
  decision says so.
- Do not add map/provider diagnostics before provider governance exists.
- Do not expose real client addresses or coordinates in docs, tests, or
  screenshots.

## 5. Cleanup Watchlist

- Quality controls inside Data Factory workflow.
- Coordinate result detail in side panels.
- Provider/settings UI without backend governance.
- Export actions not tied to persisted batch state.

## 6. Backend Contract Dependencies

- coordinate quality preview;
- batch create/list/detail;
- validation results;
- grouped issue summaries;
- export package;
- artifact/evidence metadata;
- route recovery through backend detail endpoint.

## 7. Wireframe Inputs

Required route frames:

- Quality Tools hub;
- Lat/Lon validator;
- Lat/Lon batch detail;
- export/download result state.

Required states:

- no recent batches;
- upload missing required coordinate fields;
- validation found issues;
- validation clean;
- export unavailable;
- export ready;
- direct route recovery.

## 8. Open Decisions

- Whether external provider setup is Admin, Master Data, or Developer Tools
  scope.
- Whether map diagnostics are necessary for the first redesign.
- Whether Coordinate Quality should later include more tools beyond Lat/Lon.

## 9. Acceptance For Wireframe Phase

Coordinate Quality can move to Penpot when it is accepted as a Master Data
Quality Tools flow with its own route-level batch detail and return path.
