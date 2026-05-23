# GUI Order Release Generator View

**Status:** first functional slice implemented; first row-authoring hardening slice delivered
**Branch:** `codex/gui-foundation-integration-pr-plan`

## Objective

Add the first backend-backed Order Release Generator screen using the shared GUI
foundation.

Order Release Generator now renders a staged backend-owned workflow instead of
only showing the template list.

```text
Templates -> Batch -> Preview -> Artifact -> Submit
```

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/order-release-generator/templates
GET /api/v1/modules/order-release-generator/batches
POST /api/v1/modules/order-release-generator/batches
POST /api/v1/modules/order-release-generator/batches/{batch_id}/preview-xml
POST /api/v1/modules/order-release-generator/batches/{batch_id}/generate-xml-artifact
GET /api/v1/modules/order-release-generator/batches/{batch_id}/artifacts
GET /api/v1/modules/order-release-generator/batches/{batch_id}/artifacts/{artifact_id}/download
POST /api/v1/modules/order-release-generator/batches/{batch_id}/submit-otm
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for template, required column, optional column, and default counters;
- ModuleObjectList for selectable Order Release templates;
- SelectedObjectPanel for selected template metadata;
- DetailList for required columns;
- DetailList for optional columns and defaults;
- OperationalPanel for each generator stage;
- FeedbackMessage for backend action results and guarded submit errors.
```

The first selected template defaults to the first backend item. The batch stage
creates a client-safe synthetic batch from template-guided row fields instead of
raw JSON editing. The row editor is generated from backend template
`required_columns`, `optional_columns`, and `defaults`, then submits the same
structured `rows` payload to the backend batch contract. The preview stage asks
the backend to build XML. The artifact stage asks the backend to generate the DB
XML artifact and evidence, then lists generated artifacts with a guarded backend
download action. The submit stage calls the guarded MVP0 endpoint and renders
the backend reason/capability required for future direct OTM submit.

Recent batches are read from the backend `/batches` list, so leaving the route
and returning can recover the created batch without frontend-only persistence.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only batch recovery.
- No local artifact path rendering.
- XML artifact downloads go through the backend download endpoint with hash
  verification and audit logging.
- Direct OTM submit remains guarded and disabled in MVP0.
- Template status, macro object linkage, columns, defaults, batches, XML preview,
  artifact metadata, evidence id, and submit guard details come from backend
  contracts.
```

Delivered hardening:

```text
- batch row authoring is now field-based and template-guided;
- raw JSON row editing was removed from the GUI;
- add/remove row controls keep batch input in backend contract shape;
- frontend functional QA verifies edited field payloads before batch creation.
- invalid backend batch rows now surface row-level issue code, column, severity,
  and row number inside the Batch stage;
- Preview and Artifact actions are disabled while the active batch is not VALID;
- the user can correct the row fields and recreate a valid batch without
  leaving the staged workflow.
```

Still open:

```text
- richer reusable template authoring/versioning UX
- governed direct OTM submit capability after MVP0
```

## Validation

Commands executed:

```text
cd frontend
npm run qa:functional:order-release
npm run qa:functional:order-release:browser
npm run lint
npm run build
python -m pytest tests/test_order_release_generator_batches.py
```

Recent OTM-125 validation:

```text
npm run test -- AppFunctionalOrderReleaseGenerator.test.tsx
npm run lint
npm run build
python -m pytest tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q
```

Second OTM-125 validation:

```text
npm run test -- AppFunctionalOrderReleaseGenerator.test.tsx -t "shows invalid batch row issues"
npm run test -- AppFunctionalOrderReleaseGenerator.test.tsx
npm run build
python -m pytest tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q
```
