# CSVUTIL Reference Archive Notes 2026-05-25

**Status:** sanitized reference notes
**Scope:** CSVUTIL, OTM CSV package, rates sequence, and cutover checklist test planning.

## Source Handling

The archive supplied on 2026-05-25 is treated as private reference material only.
Do not commit the ZIP, extracted CSVs, result ZIPs, CTL files, domains, emails,
GIDs, names, lane values, or any row values from the archive.

These notes intentionally record only structural observations:

```text
- package/folder shape
- table names
- file order
- column counts and row-count scale
- CSVUTIL command patterns
- QA scenarios to recreate with synthetic data
```

## Archive Shape

The archive contains four operational package groups plus a rates sequence note:

```text
- Move Agents e Refnums
- Move Master Data
- Move Misc
- Move Parameter Set
- TARIFAS_SEQ.txt
```

Each group follows the same useful package anatomy:

```text
- csvutil.ctl                 export-oriented CTL using xcsv/table filters
- csvutil.zip                 packaged input/export artifact
- csvutil.zip.result.zip      processing result artifact
- export/
  - csvutil.ctl               import-oriented CTL using ii
  - numbered TABLE.csv files
  - export.zip
  - export.zip.result.zip
```

The ZIP also contains macOS metadata entries such as `__MACOSX/`, `.DS_Store`,
and AppleDouble `._*` files. CSVUTIL package ingestion and analyzer code should
ignore these files.

## CSV Shape Observed

The CSV files follow the OTM CSV convention we already use:

```text
line 1: table name
line 2: comma-separated column names
line 3+: values
```

No `exec alter session ...` line was detected in the structural scan, even
though several exported tables include date-like columns such as `INSERT_DATE`,
`UPDATE_DATE`, `EFFECTIVE_DATE`, `EXPIRATION_DATE`, `START_DATE`, and
`START_DATETIME`.

Product rule remains:

```text
When OTM Workbench generates CSV files and any date/datetime value is present,
insert the Oracle date-format session line before the first data row.
```

The reference archive is therefore useful for import/analyzer tolerance, but it
must not weaken our generated CSV parity rule.

## CSVUTIL CTL Patterns

Two CTL modes are visible:

```text
Export CTL:
-dataFileName <NNN_TABLE.csv> -command xcsv -tableName <TABLE> -whereClause ...

Import CTL:
-dataFileName <NNN_TABLE.csv> -command ii
```

Some CTLs also contain mail notification options. The app should not preserve or
display real emails from reference material. In synthetic tests, represent this
as a sanitized `mailTo` option and verify that UI/docs do not leak addresses.

## Package Groups And Table Families

### Agents And Refnums

The reference includes a compact agent/reference-number package with tables such
as:

```text
SAVED_QUERY
SAVED_QUERY_ACCESS
SAVED_QUERY_VALUES
SAVED_CONDITION
SAVED_CONDITION_QUERY
AGENT
AGENT_EVENT
AGENT_EVENT_DETAILS
AGENT_ACTION_DETAILS
SHIPMENT_REFNUM_QUAL
ORDER_RELEASE_REFNUM_QUAL
LOCATION_REFNUM_QUAL
LOCATION_REFNUM
```

This is a good synthetic test family for:

```text
- saved query dependencies before agents
- agent event/action detail child rows
- refnum qualifier before refnum value tables
- cutover checklist grouping outside pure rates/master-data templates
```

### Master Data And Rates

The largest package combines master data, geography, equipment, service, rates,
and accessorial structures. Important table families include:

```text
Equipment:
EQUIPMENT
EQUIPMENT_TYPE
EQUIPMENT_GROUP
EQUIPMENT_TYPE_JOIN
EQUIPMENT_GROUP_PROFILE
EQUIPMENT_GROUP_PROFILE_D

Location and geography:
GEO_HIERARCHY
GEO_HIERARCHY_DETAIL
REGION
REGION_DETAIL
LOCATION
LOCATION_ADDRESS
LOCATION_PROFILE
LOCATION_ROLE_PROFILE
LOCATION_ACTIVITY_TIME_DEF
LOCATION_CORPORATION

Lane, itinerary, service:
X_LANE
ITINERARY
ITINERARY_DETAIL
LEG
RATE_SERVICE
SERVICE_TIME
RATE_SERVICE_SPEED

Rates and cost:
RATE_OFFERING
RATE_VERSION
RATE_OFFERING_REMARK
RATE_UNIT_BREAK_PROFILE
RATE_UNIT_BREAK
RATE_GEO
RATE_GEO_COST_GROUP
RATE_GEO_COST
RATE_GEO_COST_UNIT_BREAK
RATE_GEO_ACCESSORIAL
RATE_GEO_REFNUM
ACCESSORIAL_CODE
ACCESSORIAL_COST
ACCESSORIAL_COST_UNIT_BREAK
```

This package is useful for synthetic rates/cutover tests because it includes
large tables, repeated table families, parent-child relationships, and cost/unit
break dependencies.

### Misc

The misc package includes:

```text
ORDER_SCHEDULE
ORDER_SCHEDULE_D
FINDER_SET
CALENDAR
ACTIVITY_CALENDAR_OVERRIDE
```

Useful tests:

```text
- schedule parent/detail package ordering
- date/datetime column detection
- calendar dependency handling
```

### Parameter Set

The parameter package includes:

```text
PLANNING_PARAMETER_SET
PLANNING_PARAMETER
```

Useful tests:

```text
- small two-table package
- parent before detail
- high-row-count child table
```

## Rates Sequence Notes

The included rates sequence note reinforces this synthetic cutover/rates order:

```text
1. EQUIPMENT_GROUP
2. EQUIPMENT_GROUP_PROFILE
3. EQUIPMENT_GROUP_PROFILE_D
4. REGION
5. REGION_DETAIL
6. GEO_HIERARCHY
7. X_LANE
8. RATE_SERVICE
```

For LTL/TL-style rates, represent the stack with synthetic data:

```text
RATE_OFFERING
RATE_OFFERING_ACCESSORIAL
X_LANE
RATE_GEO
ACCESSORIAL_CODE
ACCESSORIAL_COST
ACCESSORIAL_COST_UNIT_BREAK
RATE_GEO_ACCESSORIAL
RATE_GEO_COST_GROUP
RATE_GEO_COST
RATE_UNIT_BREAK_PROFILE
RATE_UNIT_BREAK
RATE_GEO_COST_UNIT_BREAK
```

Additional TL coverage should include `RATE_GEO_STOPS` when the local Data
Dictionary and Oracle documentation confirm the exact dependency and required
columns.

Do not copy the literal values from the sequence note into fixtures. Convert
them into synthetic rules:

```text
- leave rate-offering sequence fields blank when OTM owns sequencing
- remove or suppress rate-geo sequence fields when not accepted by CSVUTIL
- generate rate cost group sequence deterministically
- generate rate geo cost sequence deterministically and reset per parent group
- keep base charge fields null only when the target table/calculation supports it
```

## Product Implications

### CSVUTIL Analyzer

Add or extend analyzer tests to verify:

```text
- ignores macOS metadata files [DONE first slice]
- identifies package groups
- reads CTL command mode (`xcsv`, `ii`) [DONE first slice]
- maps CTL file names to CSV files [DONE second slice]
- reads table line and header line without exposing data rows [DONE first slice]
- flags missing CSV files referenced by CTL [DONE second slice]
- flags CSV table-line mismatch with CTL table name when tableName is present [DONE second slice]
- detects nested result ZIP artifacts [DONE first slice]
- sanitizes mail notification settings [DONE third slice]
```

Implementation note, 2026-05-25:

```text
The Load Plan ZIP analyzer now accepts synthetic CSVUTIL package shapes where
CSV files live outside `csv/`, including `export/<NNN_TABLE>.csv`. It records
CTL file count, CTL command modes, ignored metadata files, and nested
`*.result.zip` artifacts in the manifest/summary without copying row values.
```

Implementation note, 2026-05-25, second slice:

```text
The analyzer now parses CSVUTIL CTL references for `-dataFileName` and
`-tableName`. It flags missing referenced CSV files and CTL table-name mismatch
against CSV line 1. These findings flow into Load Plan Review Queue as
STRUCTURE items with client-safe details only.
```

Implementation note, 2026-05-25, third slice:

```text
The analyzer now detects CTL options beginning with `mail` and stores only
sanitized option names per CTL file. It does not persist or return addresses,
subjects, or notification values.
```

### Cutover Checklist

The cutover checklist should support package-family readiness:

```text
- Agents/Refnums package
- Master Data/Rates package
- Misc operational setup package
- Planning Parameter package
```

Each package should produce checklist items for:

```text
- CTL parsed
- CSV file count matches CTL
- table order matches Catalog/Data Dictionary dependency plan
- date/datetime CSV parity checked
- result ZIP attached or expected as post-run evidence
- blocked items reviewed before Go/No-Go [DONE first readiness slice]
```

Implementation note, 2026-05-25, cutover readiness first slice:

```text
Cutover Checklist readiness now considers the latest ZIP analysis for the
package. ERROR findings block readiness and WARNING findings move readiness to
review, even when manual checklist items are DONE. The readiness payload
includes only client-safe finding details and analyzer counts.
```

### Rates And Master Data Tests

Use the archive only to design synthetic scenarios:

```text
- high-row-count rates cost/unit break tables
- accessorial cost with unit break children
- rate offering -> rate geo -> rate geo cost group -> rate geo cost hierarchy
- equipment group profile dependencies
- location/region/geography dependencies
```

## Follow-Up Issues

Recommended Linear/backlog follow-ups:

```text
1. CSVUTIL analyzer: parse CTL/CSV package structure with synthetic fixtures.
   [FIRST SLICE DELIVERED: generic CSV discovery, CTL mode scan, ignored
   metadata, nested result ZIP detection]
2. Cutover checklist: package-family readiness from CTL/CSV analyzer output.
   [FIRST SLICE DELIVERED: latest ZIP analysis findings now feed readiness
   blockers/review state]
3. Rates QA: synthetic LTL/TL rate stack based on the observed table sequence.
4. Master Data QA: synthetic location/equipment/geography package family.
5. Security: ensure reference archives and generated QA artifacts never leak
   real domains, emails, GIDs, local paths, or row values.
```
