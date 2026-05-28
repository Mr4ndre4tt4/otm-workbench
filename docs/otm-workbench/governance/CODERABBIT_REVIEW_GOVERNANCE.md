# CodeRabbit Review Governance

**Status:** active assistive review policy
**Date:** 2026-05-27

## Purpose

CodeRabbit is an assistive reviewer for OTM Workbench. It is useful as a second
reader for broad PRs, risky implementation slices, CI/workflow changes,
security-sensitive changes, and governance changes.

CodeRabbit does not replace Solon, tests, GitHub Actions, browser QA, or human
judgment. It is not a required merge gate in the current phase.

## Current Policy

Use CodeRabbit when:

- a PR changes backend behavior, frontend workflow, CI, governance, or security
  boundaries;
- the diff is large enough that a second review pass is valuable;
- the user asks for review, quality feedback, or risk scanning;
- a future merge decision would benefit from an independent issue list.

Do not use CodeRabbit when:

- the change is a tiny doc or typo fix;
- it would delay urgent context preservation;
- it is likely to review only generated or local-only files;
- it starts producing noisy comments that do not improve the project.

## Operating Rules

- Treat CodeRabbit output as review input, not truth.
- Convert valid findings into GitHub comments, issues, commits, or documented
  deferrals.
- Do not blindly implement suggestions. Check them against `AGENTS.md`,
  `docs/agent/CURRENT_SCOPE.md`, and module specs.
- Do not let CodeRabbit reintroduce excluded top-level UI modules or weaken the
  current UI phase boundary.
- Do not expose or commit protected local `OTM_RESOURCES/` content to make
  CodeRabbit or CI happy.

## Configuration

The repository uses `.coderabbit.yaml` at the root. The config:

- excludes local/protected artifacts, build output, binaries, and generated
  evidence from review;
- keeps automatic review enabled for ready PRs;
- skips draft PR auto-review by default to avoid noisy early feedback;
- adds path-specific review instructions for backend, frontend, tests, GitHub
  workflows, and governance docs.

If the team wants CodeRabbit to review draft PRs, change:

```yaml
reviews:
  auto_review:
    drafts: true
```

Only do this after proving the feedback is useful on real PRs.

## CLI Use

Use the CLI for intentional review passes:

```powershell
coderabbit --version
coderabbit auth status --agent
coderabbit review --agent --base main
```

If `coderabbit` is not installed or authenticated, do not treat CodeRabbit as a
required validation step. Record the limitation and use GitHub Actions plus
human/Solon review.

## Acceptance Bar

CodeRabbit is helping when:

- it finds real bugs, regression risks, or missing tests;
- it reduces review blind spots;
- its comments are few enough to act on;
- accepted findings are linked to commits or issues.

CodeRabbit is hurting when:

- it duplicates obvious checklist items;
- it comments heavily on historical docs or generated artifacts;
- it blocks delivery without identifying real risk;
- reviewers start treating its output as a replacement for project context.
