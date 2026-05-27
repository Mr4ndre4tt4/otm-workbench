# Synthetic Fixture Pack

Status: active synthetic baseline

These files are safe test fixtures for OTM Workbench backend, QA, and module
planning slices. They do not contain client data.

Scope conventions:

- project: `SYNTHETIC_PROJECT`
- environment: `UAT`
- domain: `OTM1`
- visibility: `PRIVATE` unless a fixture explicitly says `PUBLIC`

The OTM CSV samples keep the CSVUTIL-like shape expected by the project:

1. first line is the table name;
2. second line contains columns;
3. if date fields are present, an `exec alter session ...` line appears before
   data rows;
4. following lines are values.

Use these fixtures as small baseline files. Module-specific performance or edge
tests may create larger generated fixtures in a separate scenario folder.
