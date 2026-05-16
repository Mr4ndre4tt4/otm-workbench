# project-framework Design

## Status

Approved for implementation planning.

## Summary

`project-framework` is a reusable Codex plugin for general software projects. It provides a technical governance framework made of independent skills, rigid Markdown templates, and shared artifact contracts. The plugin is not tied to `otm_workbench` or any specific application.

The framework is designed for projects where Codex should leave versioned, auditable documentation while helping teams control architecture, engineering standards, code review quality, QA/regression, scalability, and security.

## Goals

- Provide a reusable Codex plugin for any software project.
- Use independent skills that can be invoked directly.
- Keep all generated project artifacts in Markdown.
- Maintain a root `PROJECT.md` as the central project index and status surface.
- Store domain artifacts under existing project documentation areas such as `docs/architecture/`, `docs/qa/`, and `docs/security/`.
- Use rigid templates with required sections and checklists.
- Write skill instructions in English and generated project artifacts in Portuguese by default.
- Support both project-level governance and feature/epic-level execution.

## Non-Goals

- Build an `otm_workbench` application.
- Create a web dashboard.
- Create a single orchestration skill that controls all other skills.
- Replace issue trackers, CI systems, test frameworks, or security scanners.
- Store all framework artifacts in a single `docs/otm/` folder.

## Plugin Name

The plugin name is:

```text
project-framework
```

The original suggested name `project_framework` is normalized to Codex plugin naming conventions: lowercase, hyphen-delimited.

## Architecture

The plugin uses independent skills with a shared artifact contract.

```text
project-framework/
  .codex-plugin/
    plugin.json
  skills/
    technical-diagnosis/
      SKILL.md
    architecture-governance/
      SKILL.md
    engineering-standards/
      SKILL.md
    code-review-governance/
      SKILL.md
    qa-regression/
      SKILL.md
    scalability-review/
      SKILL.md
    security-review/
      SKILL.md
  references/
    artifact-contract.md
    project-index-contract.md
  templates/
    project.md
    status-fields.md
    checklists/
```

Each skill can be used independently. Shared references and templates define the common rules for artifact structure, status fields, naming, checklists, and `PROJECT.md` updates.

## Operating Model

The framework is hybrid:

- It supports a project-level journey through technical diagnosis, architecture, standards, QA, scalability, security, and release-readiness concerns.
- Each skill can also be invoked directly for a focused task.

The journey is adaptive. The first recommended step is a technical diagnosis that evaluates:

- type of system
- architecture
- stack
- integrations
- data flows
- technical risks

The diagnosis recommends the level of rigor and which skills should be applied next.

## Project Artifact Layout

Projects using the plugin should keep a central project index at the repository root:

```text
PROJECT.md
```

Domain artifacts should live under domain-specific folders:

```text
docs/
  architecture/
  engineering/
  qa/
  scalability/
  security/
```

The framework uses a hybrid versioning model:

- Live files hold the current state.
- Dated records preserve decisions, reviews, risks, evidence, and audit history.

Example live files:

```text
docs/architecture/overview.md
docs/engineering/standards.md
docs/qa/test-strategy.md
docs/security/security-posture.md
docs/scalability/scalability-plan.md
```

Example dated records:

```text
docs/architecture/decisions/YYYY-MM-DD-adr-title.md
docs/engineering/reviews/YYYY-MM-DD-code-review.md
docs/qa/regression-runs/YYYY-MM-DD-feature-or-release.md
docs/security/reviews/YYYY-MM-DD-security-review.md
docs/scalability/reviews/YYYY-MM-DD-scalability-review.md
```

## PROJECT.md Contract

Every skill must create or update `PROJECT.md`.

Required sections:

```text
# Projeto

## Status Atual
## Mapa de Artefatos
## Decisões Recentes
## Riscos Abertos
## Próximos Passos
## Histórico de Execuções do Framework
```

`PROJECT.md` is the central navigation and status artifact. It must link to generated domain artifacts, summarize active risks, and record the latest framework executions.

## Common Artifact Contract

All generated Markdown artifacts must use rigid templates with required sections.

Required sections:

```text
# <Título>

## Status
## Escopo
## Contexto
## Achados ou Decisões
## Riscos
## Ações Recomendadas
## Checklist
## Links Relacionados
## Última Atualização
```

Skills may add domain-specific sections, but they must not omit required sections. If a section has no content, the skill must explicitly state that no relevant item was identified.

## Initial Skills

### technical-diagnosis

Evaluates system type, architecture, stack, integrations, data flows, and technical risks. It recommends the project rigor level and the next skills to run.

Primary artifacts:

```text
PROJECT.md
docs/engineering/technical-diagnosis.md
```

### architecture-governance

Documents current or proposed architecture, architectural decisions, trade-offs, dependencies, integrations, and technical risks.

Primary artifacts:

```text
docs/architecture/overview.md
docs/architecture/decisions/YYYY-MM-DD-adr-title.md
```

### engineering-standards

Defines engineering standards for code structure, tests, branches, commits, observability, configuration, dependencies, and definition of done.

Primary artifacts:

```text
docs/engineering/standards.md
```

### code-review-governance

Guides technical review of changes with focus on bugs, regressions, risks, standard adherence, and test gaps.

Primary artifacts:

```text
docs/engineering/reviews/YYYY-MM-DD-code-review.md
```

### qa-regression

Defines test strategy, regression matrix, acceptance criteria, validation plan, and evidence expectations.

Primary artifacts:

```text
docs/qa/test-strategy.md
docs/qa/regression-runs/YYYY-MM-DD-feature-or-release.md
```

### scalability-review

Evaluates performance, bottlenecks, known limits, capacity, cost, caching, queues, databases, and growth risks.

Primary artifacts:

```text
docs/scalability/scalability-plan.md
docs/scalability/reviews/YYYY-MM-DD-scalability-review.md
```

### security-review

Evaluates authentication, authorization, sensitive data, secrets, dependencies, API exposure, logs, abuse cases, and security risks.

Primary artifacts:

```text
docs/security/security-posture.md
docs/security/reviews/YYYY-MM-DD-security-review.md
```

## Language Policy

- Skill instructions are written in English.
- Generated project artifacts are written in Portuguese by default.
- Folder and file names are written in English for interoperability.

## Validation Expectations

During implementation, the plugin should be validated by:

- Checking every skill has valid `SKILL.md` frontmatter.
- Checking every skill references the shared artifact contract.
- Running skill validation tooling from the skill creator workflow.
- Testing at least one generated artifact path per skill.
- Verifying that every skill updates `PROJECT.md`.

## Implementation Notes

The implementation should use the Codex plugin structure:

```text
.codex-plugin/plugin.json
skills/*/SKILL.md
references/
templates/
```

The implementation should keep `SKILL.md` files concise and put reusable templates or detailed standards into `references/` and `templates/`.

## Open Questions

None for the current design. Details such as exact template prose, status enum values, and skill trigger descriptions should be finalized during implementation planning.
