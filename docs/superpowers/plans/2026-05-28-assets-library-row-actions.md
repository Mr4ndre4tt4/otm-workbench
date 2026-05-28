# Assets Library Row Actions Plan

## Goal

Make `/assets/library` search results provide explicit route-level actions while
preserving the existing selected-asset workflow.

## Steps

1. Add a failing functional test for row action links.
2. Render library results with action-capable rows.
3. Add row actions for select, open, upload version, and archive.
4. Re-run focused and full Assets functional tests.
5. Run frontend build and browser QA.
6. Update validation and handoff docs.
