# Michelangelo Wireframe Brief - Assets Library

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/ASSETS_LIBRARY_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Controlled asset, version, metadata, classification, and link management.

Primary user task:
Create, find, version, link, download, and archive project assets safely.

User profile:
Consultant, implementation lead, admin-adjacent asset owner.

Task criticality:
Medium to high. Incorrect assets or links can break evidence, schema, and module
traceability.

Input reviewed:
Assets Library consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns metadata validation, classifications, links, available actions,
version state, and archive guards.

## 2. Archetypes

- artifact/library manager;
- CRUD form;
- version history;
- link builder;
- critical archive confirmation.

## 3. Route Inventory For Wireframes

```text
/assets
/assets/library
/assets/new
/assets/:assetId
/assets/:assetId/edit
/assets/:assetId/versions
/assets/:assetId/versions/new
/assets/:assetId/links
/assets/classifications
/assets/classifications/new
/assets/classifications/:classificationId/edit
/assets/:assetId/archive
```

## 4. UX Findings To Design Around

ID:
ASSET-UX-01

Severity:
P1 High

Category:
Workflow and grouping

Where:
Asset creation and classification authoring.

Evidence:
The spec says not to mix classification authoring with asset creation.

Problem:
Combining metadata, classification creation, upload, links, and list views can
make asset creation feel like a generic file manager.

User impact:
Inconsistent metadata and invalid asset organization.

Recommendation:
Wireframe asset creation as focused metadata plus optional upload next step;
classification authoring gets its own route.

Acceptance criteria:
Asset creation does not contain classification administration controls.

---

ID:
ASSET-UX-02

Severity:
P1 High

Category:
Error prevention

Where:
Asset links and archive.

Evidence:
Links must be backend-validated and archived assets reject mutation.

Problem:
Ungoverned link controls can create broken references to modules, OTM tables,
evidence, or artifacts.

User impact:
Bad traceability and failed downstream workflows.

Recommendation:
Use guided backend-owned target selection and archive impact review.

Acceptance criteria:
Invalid link targets and archived mutation attempts show clear backend reasons.

## 5. Required Wireframe States

- no assets;
- metadata validation error;
- upload pending;
- upload blocked;
- invalid link target;
- target lookup empty;
- archived asset;
- system classification protected.

## 6. Wireframe Acceptance Criteria

- Asset lifecycle is separate from classification lifecycle.
- Versions, links, and archive are route-level.
- Backend-owned target types are visible.
- Archived assets cannot show mutation as available.
- No local paths or unsafe downloads appear.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for file-manager drift;
- asset link validation QA plan;
- archive mutation guard checklist.
