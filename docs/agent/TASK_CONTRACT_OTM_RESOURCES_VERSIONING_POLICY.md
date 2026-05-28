# Task Contract: OTM_RESOURCES Versioning Policy

## Objective

Define the repository policy for local `OTM_RESOURCES` content before any raw
resource files are added to GitHub.

## Original User Request

Continue the roadmap and address whether `OTM_RESOURCES/` should be uploaded to
GitHub, excluding customer-bearing `db.xml` files and after a sensitivity double
check.

## Interpreted Scope

- Inventory the local `OTM_RESOURCES` classes without copying client payloads
  into docs.
- Record which resource classes are blocked, conditionally allowed, or safe only
  after explicit approval.
- Add ignore rules to prevent accidental public upload of raw OTM resources.
- Add an environment example so clean worktrees can point at the local Data
  Dictionary.
- Align low-level rates tests with the same configured Data Dictionary path
  used by application routes.
- Validate the policy with Git ignore checks and backend tests that depend on
  the Data Dictionary.

## Out Of Scope

- Uploading `OTM_RESOURCES` content in this slice.
- Sanitizing or transforming Oracle/vendor reference packs.
- Reviewing or changing Integration Mapping implementation.
- Moving, deleting, or archiving local resource files.

## Allowed Files Or Areas

- `.gitignore`
- `.env.example`
- `docs/agent/OTM_RESOURCES_VERSIONING_POLICY.md`
- `docs/agent/TASK_CONTRACT_OTM_RESOURCES_VERSIONING_POLICY.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- rates tests that hardcode the default local Data Dictionary path

## Protected Files Or Areas

- `OTM_RESOURCES/` raw content.
- `*.db.xml` exports.
- Application source files and migrations.
- Integration Mapping workstream files except for passive documentation
  references that already exist.

## Acceptance Criteria

- The policy explains why raw resources are not committed to the public
  repository now.
- Sensitive `db.xml` exports and raw `OTM_RESOURCES/` are ignored.
- A future allowlist process exists for private or sanitized resource
  versioning.
- Validation proves the documented external Data Dictionary path works from a
  clean worktree.
- Rates tests that need the Data Dictionary use `get_settings()` rather than a
  hardcoded local path.

## Validation Plan

- `git check-ignore -v` against local `OTM_RESOURCES` and `*.db.xml` paths.
- `python -m pytest tests/test_rates_dictionary.py tests/test_modules_navigation.py -q`
  with `OTM_OTM_DATA_DICTIONARY_ROOT` pointing at the local Data Dictionary.
- `git diff --check`.

## Risks

- Data Dictionary and XLS files may be useful but may also be vendor-licensed
  material unsuitable for a public GitHub repository.
- `db.xml` exports can contain operational records even when they look small or
  synthetic.
- Ignoring the full directory means contributors must configure the environment
  variable locally until a governed resource distribution exists.

## Challenge Notes

Because the repository is public, "not customer data" is not enough to justify
uploading raw resources. Vendor license/provenance and sanitization must also be
clear.

## Decision

Proceed with policy, ignore rules, and validation. Do not upload raw
`OTM_RESOURCES` content in this slice.
