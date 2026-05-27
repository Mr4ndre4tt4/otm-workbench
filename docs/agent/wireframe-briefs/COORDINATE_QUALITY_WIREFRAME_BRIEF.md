# Michelangelo Wireframe Brief - Coordinate Quality

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/COORDINATE_QUALITY_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Master Data quality utility for Location coordinate validation.

Primary user task:
Upload or inspect Location coordinate data, review validation issues, and export
a correction/review package.

User profile:
Functional consultant, master data lead.

Task criticality:
Medium to high. Incorrect coordinates can affect planning, distance, and
quality review.

Input reviewed:
Master Data redesign spec, coordinate quality design, and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Coordinate Quality remains under Master Data / Quality Tools and backend owns
batches, results, and export readiness.

## 2. Archetypes

- quality utility;
- data validation workspace;
- result detail;
- artifact export.

## 3. Route Inventory For Wireframes

```text
/master-data/quality
/master-data/quality/lat-lon
/master-data/quality/lat-lon/batches/:batchId
```

## 4. UX Findings To Design Around

ID:
CQ-UX-01

Severity:
P1 High

Category:
Information architecture

Where:
Master Data route family.

Evidence:
The Master Data redesign explicitly separates Quality Tools from Data Factory.

Problem:
If Lat/Lon appears as a Data Factory stage, users may think coordinate
validation is required for every CSV export.

User impact:
Wrong task path and unnecessary friction.

Recommendation:
Wireframe Coordinate Quality only under Quality Tools with clear return path.

Acceptance criteria:
No Coordinate Quality control appears in operational Data Factory flow.

---

ID:
CQ-UX-02

Severity:
P2 Medium

Category:
Feedback and result inspection

Where:
Lat/Lon batch detail.

Evidence:
The current route stores persisted validation results and exports correction
packages.

Problem:
Result tables without issue grouping or export readiness can be hard to act on.

User impact:
Users may not know what to fix or whether a package is ready.

Recommendation:
Wireframe grouped issue summary, row-level results, export readiness, and
artifact/evidence references.

Acceptance criteria:
Users can identify issue type, affected rows, and export availability.

## 5. Required Wireframe States

- no recent coordinate batches;
- upload missing coordinate fields;
- validation running;
- validation issues found;
- clean validation;
- export blocked;
- export ready;
- direct batch route recovery.

## 6. Wireframe Acceptance Criteria

- Coordinate Quality is visibly a Master Data quality utility.
- Result detail is route-level with Back to Quality Tools.
- Issues are grouped and actionable.
- Export is tied to persisted batch state.
- No real addresses or client coordinates appear.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for quality-tool separation;
- browser QA plan for upload, result, export, and direct route recovery;
- client-data safety review for coordinate examples.
