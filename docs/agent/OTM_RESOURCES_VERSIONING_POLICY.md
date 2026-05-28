# OTM_RESOURCES Versioning Policy

## Current Decision

Do not commit raw `OTM_RESOURCES/` content to the public GitHub repository.

The repository is public, and the local resource directory contains a mix of:

- Oracle OTM Data Dictionary 26B reference material;
- operator/operand spreadsheet resources;
- `*.db.xml` exports and seed payloads.

Even when a file is not client data, it can still be unsafe for the public repo
because it may be vendor-licensed material, operational export data, or an
unsanitized fixture.

## Local Inventory Summary

Observed local resource classes:

| Resource class | Observed examples | Current policy |
|---|---|---|
| Data Dictionary 26B JSON/HTML/TXT assets | `DATA_DICT26B/...` | Keep local. May become a private artifact or explicit allowlist item only after license/provenance review. |
| Operator/operand spreadsheets | `RATABLE_OPERATOR.xls`, `RATE_GEO_COST_OPERAND.xls` | Keep local until converted or reviewed. Binary XLS files need provenance and sensitivity review before versioning. |
| OTM `db.xml` exports | `dbXmlExport_*.db.xml`, `sample_lookup_seed.db.xml` | Do not commit raw exports. Use sanitized synthetic fixtures only. |

The local Data Dictionary JSON folder contains table metadata needed by backend
validation. Clean worktrees should point to it with:

```powershell
$env:OTM_OTM_DATA_DICTIONARY_ROOT='C:\Users\Enzo Trabalho\Documents\New project 3\OTM_RESOURCES\DATA_DICT26B\data_dictionary\json\data_dict'
```

## Versioning Rules

Blocked from the public repository:

- raw `OTM_RESOURCES/`;
- any `*.db.xml` export;
- raw Oracle/vendor documentation packs without explicit license clearance;
- binary spreadsheets until provenance and contents are reviewed;
- any file containing real customer, domain, lane, credential, user, or
  production operational values.

Allowed with normal review:

- small synthetic fixtures under `tests/fixtures/`;
- generated docs that describe resource handling without embedding proprietary
  or customer payloads;
- sanitized extracts that contain only invented values and have a documented
  generation path.

Conditionally allowed after explicit approval:

- a private GitHub release artifact;
- a Git LFS resource pack in a private repo;
- a curated allowlist under `OTM_RESOURCES/` after license, provenance,
  sensitivity, and size review.

## Required Checks Before Any Future Upload

1. Confirm repository visibility and target audience.
2. Confirm license/provenance for vendor/reference files.
3. Scan for customer, domain, email, credential, token, password, and
   production-like values.
4. Prefer synthetic fixtures or generated extracts over raw exports.
5. Update `.gitignore`, this policy, `HANDOFF.md`, and `VALIDATION_REPORT.md`.
6. Open or update a GitHub Issue before adding resource files.

## Operational Guidance

Developers running resource-dependent tests from a clean worktree must configure
`OTM_OTM_DATA_DICTIONARY_ROOT`. A template is available in `.env.example`.

Do not remove the local `OTM_RESOURCES` directory during cleanup. It is a local
dependency until the project adopts a governed private artifact strategy.
