# Master Data / Data Factory Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`
**Evidence:** `docs/otm-workbench/gui/GUI_MASTER_DATA_REDESIGN_COMPLETION_REVIEW_2026_05_26.md`

## 1. Original Intent

Master Data / Data Factory exists to turn implementation master-data work into
a controlled OTM load preparation flow:

- choose or author reusable templates;
- collect operator-friendly data;
- validate structure, relationships, and dependencies;
- convert data into OTM table records;
- generate CSV/ZIP packages with manifest and evidence;
- hand off validated packages to Load Plan;
- keep all OTM table and field decisions validated through the Data Dictionary.

The foundation docs define this as an operational journey, not as a generic
spreadsheet utility or technical table editor.

## 2. Current Evidence

The current redesign spec and completion review show that the UI has already
moved away from a single overloaded staged screen. Delivered route families:

```text
/master-data
/master-data/factory
/master-data/factory/templates/:templateCode
/master-data/factory/batches/:batchId
/master-data/template-builder
/master-data/template-builder/new
/master-data/template-builder/:templateCode
/master-data/template-builder/:templateCode/edit
/master-data/template-builder/:templateCode/copy
/master-data/template-builder/:templateCode/delete
/master-data/quality
/master-data/quality/lat-lon
/master-data/quality/lat-lon/batches/:batchId
```

The dynamic template factory spec records backend-owned template authoring,
versioning, validation, one-to-many mappings, fixed/default values, runtime CSV
generation, and Data Dictionary traceability.

## 3. Validated Target Scope

For Penpot and future implementation planning, Master Data should be treated as
one module with three separate route families:

1. **Data Factory**
   Published-template consumption, workbook/editor input, batch validation,
   output records, CSV/ZIP export, guarded artifact download, and Load Plan
   handoff.

2. **Template Builder**
   Draft/published template list, search, create, detail, edit, copy, guarded
   retire/delete impact, validation, versioning, publish, and Data
   Dictionary-backed mapping.

3. **Quality Tools**
   Location coordinate quality utilities, starting with Lat/Lon validation,
   persisted batch detail, result inspection, and correction package export.

The module hub must help the user choose the correct job before seeing detailed
workflow controls.

## 4. Explicit Non-Scope

- Do not merge Data Factory, Template Builder, and Quality Tools into one
  staged workflow.
- Do not make Lat/Lon a Data Factory export step.
- Do not expose field-by-field technical authoring inside operational template
  consumption screens.
- Do not create direct OTM submit until connection, credential, capability,
  audit, retry/job, and Oracle transport governance exist.
- Do not expose real client data or local artifact paths.

## 5. Cleanup Watchlist

Future cleanup planning should look for:

- legacy `Data Factory workflow` strips that still imply one mixed journey;
- selected-object side panels that contain core object detail or actions;
- authoring controls visible inside operational batch/template screens;
- quality controls inside Data Factory export flow;
- field card walls that should be dense tables or focused route-level editors;
- frontend-only assumptions for template validity, action availability, or
  blocked reasons.

No cleanup is approved by this review.

## 6. Backend Contract Dependencies

Wireframes should assume backend ownership for:

- template list/detail/search;
- template available actions and disabled reasons;
- draft create/update/validate/publish/version/copy;
- workbook build and guarded download;
- workbook editor validation and batch creation;
- batch detail, available actions, and lifecycle;
- relationship validation, mapping, output build, CSV build, package export;
- Load Plan package registration;
- Coordinate Quality preview, validation batch detail, result, and export.

## 7. Wireframe Inputs

Required route frames:

- Master Data hub;
- Data Factory template list;
- published template detail;
- batch execution detail;
- Template Builder list/search;
- new template wizard;
- template detail;
- template edit;
- template copy;
- template delete/retire impact;
- Quality Tools hub;
- Lat/Lon validator;
- Lat/Lon batch detail.

Required state frames:

- no published templates;
- template unavailable or permission-blocked;
- batch before validation;
- validation blockers;
- export blocked;
- exported package ready;
- Load Plan registration exists;
- empty Template Builder;
- invalid template definition;
- copy created;
- delete/retire blocked by active batches;
- no recent coordinate batches;
- coordinate validation result with issues.

## 8. Open Decisions

- Whether Template Builder should be a top-level module later or remain inside
  Master Data as a route family.
- Whether immutable template version history is required before module-complete
  status.
- Which official Oracle documentation references should be required for the
  first dynamic templates beyond Data Dictionary validation.
- How far browser-based spreadsheet editing should go before it becomes a
  separate governed feature.

## 9. Acceptance For Wireframe Phase

Master Data can move to Figma wireframing when:

- the user accepts this target scope;
- the wireframe brief is reviewed;
- the Penpot page keeps operational, authoring, and quality workflows separate;
- cleanup candidates remain tracked but not executed.
