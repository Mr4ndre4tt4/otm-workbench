# Repository Recovery Plan

**Status:** proposed, no archive actions performed
**Date:** 2026-05-26

## Mission

Stabilize project context before more development. Recovery should make active
docs easy to find, preserve historical evidence, and prevent stale docs from
driving future work.

## Non-Destructive Rules

- Do not delete files.
- Do not rewrite history.
- Do not mass-move files without approval.
- Do not archive source code without explicit approval.
- Prefer reversible documentation archive.
- Preserve evidence and rationale.

## Recovery Flow

1. Maintain `docs/agent/` as the active governance entry layer.
2. Complete file-by-file inventory for docs.
3. Mark each doc as active, supporting, superseded, duplicate, unknown, or
   archive-candidate.
4. Review archive candidates with the user.
5. Move approved docs to `archive/YYYY-MM-DD/deprecated-docs/`.
6. Create `archive/YYYY-MM-DD/INDEX.md`.
7. Update `DOCUMENT_INVENTORY.md`.
8. Update `AGENTS.md` and module indexes if references change.

## Current Archive Candidates

Path:
`docs/otm-workbench/gui/*_VIEW.md`

Classification:
supporting, possible archive-candidate later

Reason:
Many modules now have consolidated route-level specs. Older view docs may be
historical evidence rather than active direction.

Recommended action:
Review each file against its consolidated spec before archiving.

Destination:
`archive/YYYY-MM-DD/deprecated-docs/gui/view-contracts/`

Risk:
Some view docs may contain details not yet moved into consolidated specs.

Needs user confirmation:
Yes

---

Path:
`docs/otm-workbench/gui/*_QA_ATTEMPT.md`

Classification:
unknown, possible archive-candidate later

Reason:
Attempt docs may be superseded by completed QA pass or visual QA docs.

Recommended action:
Compare each attempt doc with current QA evidence before archiving.

Destination:
`archive/YYYY-MM-DD/deprecated-docs/gui/qa-attempts/`

Risk:
Attempt docs may explain unresolved gaps.

Needs user confirmation:
Yes

---

Path:
`docs/otm-workbench/gui/GUI_*_EXTRACTION.md`

Classification:
unknown, possible archive-candidate later

Reason:
Extraction notes may be replaced by active pattern contracts and design-system
handoff docs.

Recommended action:
Review whether each extraction doc still informs active contracts.

Destination:
`archive/YYYY-MM-DD/deprecated-docs/gui/extraction-notes/`

Risk:
Token and style decisions may be lost if not summarized first.

Needs user confirmation:
Yes

---

Path:
`docs/otm-workbench/roadmap/backlog_pos_rates.md`

Classification:
unknown

Reason:
It may conflict with the new phased roadmap or may contain useful historical
post-Rates backlog decisions.

Recommended action:
Reconcile with `docs/agent/ROADMAP.md` and either keep as supporting history or
archive with a replacement note.

Destination:
`archive/YYYY-MM-DD/deprecated-docs/roadmap/`

Risk:
Could contain unresolved work not yet copied into the new roadmap.

Needs user confirmation:
Yes

## Immediate Recommendation

Do not archive anything yet. First complete the module scope validation pass,
then archive docs whose replacement is explicit.
